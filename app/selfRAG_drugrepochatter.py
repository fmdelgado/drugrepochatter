
import json
import re
import logging
from typing import List, Any
from typing_extensions import TypedDict

from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langgraph.graph import END, StateGraph, START

# from app.ollama_connector import ollama_embeddings, ollama_llm
# Or wherever you import your LLM from
from ollama_connector import ollama_llm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -------------------------------------------
#  LLM Setup
# -------------------------------------------
llm = ollama_llm


# -------------------------------------------
#  Prompt Setup
# -------------------------------------------
prompt = PromptTemplate(
    template="""You are a grader assessing relevance of a retrieved document to a user question. \n 
    Here is the retrieved document: \n\n {document} \n\n
    Here is the user question: {question} \n
    If the document contains keywords related to the user question, grade it as relevant. \n
    It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question. \n
    Provide the binary score as a JSON with a single key 'score' and no premable or explanation.""",
    input_variables=["question", "document"],
)
retrieval_grader = prompt | llm | JsonOutputParser()


def format_docs(docs):
    """Helper to join doc content if needed by grader."""
    return "\n\n".join(doc.page_content for doc in docs)


# Adjust the prompt to include citation instructions and example
prompt_template = """You are an assistant that answers questions based on the provided context.

Context:
{context}

Question:
{question}

**It is crucial that you only answer based on the provided context.** Provide a concise answer to the question based solely on the context above. **After every sentence or factual statement, include a citation in the format [Source X].** Use the Source IDs provided in the context and sources list.

**If you cannot answer the question based on the context, respond with:** "I'm sorry, but the documents do not contain information about your question."

For example:
"A musculoskeletal condition affects the muscles, bones, and joints [Source 1]."

Answer:
"""
rag_prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
rag_chain = rag_prompt | llm | StrOutputParser()


def map_citations_to_sources(generation, documents):
    """Match [Source X] citations in generation to actual document chunks."""
    generation_text = generation.strip()

    citation_pattern = r'\[Source\s*(\d+)\]'
    citations = re.findall(citation_pattern, generation_text)
    unique_citations = set(citations)

    source_mapping = {}
    for citation in unique_citations:
        idx = int(citation) - 1  # zero-based
        if 0 <= idx < len(documents):
            source_mapping[f"Source {citation}"] = documents[idx]
        else:
            logger.warning(f"Invalid citation [Source {citation}]")

    return source_mapping


# -------------------------------------------
#  Hallucination Grader
# -------------------------------------------
hallucination_prompt = PromptTemplate(
    template="""You are a grader assessing whether an answer is grounded in / supported by a set of facts. \n 
    Here are the facts:
    \n ------- \n
    {documents} 
    \n ------- \n
    Here is the answer: {generation}
    Give a binary score 'yes' or 'no' score to indicate whether the answer is grounded in / supported by a set of facts. \n
    Provide the binary score as a JSON with a single key 'score' and no preamble or explanation.""",
    input_variables=["generation", "documents"],
)
hallucination_grader = hallucination_prompt | llm | JsonOutputParser()


# -------------------------------------------
#  Answer Grader
# -------------------------------------------
answer_grader_prompt = PromptTemplate(
    template="""You are a grader assessing whether an answer is useful to resolve a question. \n 
    Here is the answer:
    \n ------- \n
    {generation} 
    \n ------- \n
    Here is the question: {question}
    Give a binary score 'yes' or 'no' to indicate whether the answer is useful to resolve a question. \n
    Provide the binary score as a JSON with a single key 'score' and no preamble or explanation.""",
    input_variables=["generation", "question"],
)
answer_grader = answer_grader_prompt | llm | JsonOutputParser()


# -------------------------------------------
#  Question Re-writer
# -------------------------------------------
re_write_prompt = PromptTemplate(
    template="""You a question re-writer that converts an input question to a better version that is optimized 
for vectorstore retrieval. Look at the initial question and formulate an improved question. 
Here is the initial question:

{question}

Output only the improved question with no preamble or explanation.""",
    input_variables=["question"],
)
question_rewriter = re_write_prompt | llm | StrOutputParser()


# -------------------------------------------
#  Define the Graph State + Node Functions
# -------------------------------------------
class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: the user's question
        generation: the final LLM answer
        documents: list of doc chunks
        retriever: the retriever object to be used (added here so it can be passed around)
    """
    question: str
    generation: str
    documents: List[Any]   # Typically a list of Document objects
    retriever: Any


def transform_query(state):
    """
    Optional step to re-write the question for better retrieval.
    """
    logger.info("---TRANSFORM QUERY---")
    original_question = state["question"]
    better_question = question_rewriter.invoke({"question": original_question})

    # Return updated question
    state["question"] = better_question
    return state


def retrieve(state):
    logger.info("---RETRIEVE---")
    question = state["question"]
    retriever = state["retriever"]

    # This calls retriever.invoke(...) with some default k=50,
    # or you can let the retriever handle k internally if it's set.
    documents = retriever.invoke(question, k=5)

    state["documents"] = documents
    return state


def grade_documents(state):
    logger.info("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state["documents"]

    filtered_docs = []
    for doc in documents:
        try:
            response = retrieval_grader.invoke(
                {"question": question, "document": doc.page_content}
            )

            # Attempt to parse "score"
            grade = None
            if isinstance(response, dict) and "score" in response:
                # If it returned a dict
                grade = response["score"]
            else:
                # Try to find JSON in the response string
                json_match = re.search(r"\{.*?}", str(response))
                if json_match:
                    try:
                        response_json = json.loads(json_match.group(0))
                        grade = response_json.get("score")
                    except json.JSONDecodeError:
                        grade = None
                else:
                    # Fallback: check for "yes" / "no" in text
                    resp_lower = str(response).lower()
                    if "yes" in resp_lower:
                        grade = "yes"
                    elif "no" in resp_lower:
                        grade = "no"

            if grade and grade.lower() == "yes":
                logger.info(f"---GRADE: DOCUMENT RELEVANT--- Source={doc.metadata.get('source', 'N/A')} ")
                filtered_docs.append(doc)
            elif grade and grade.lower() == "no":
                logger.info(f"---GRADE: DOCUMENT NOT RELEVANT--- Source={doc.metadata.get('source', 'N/A')} ")
            else:
                logger.warning(f"---WARNING: Could not determine relevance. Response: {response}")

        except Exception as e:
            logger.error(f"---ERROR: Error grading document: {e}")

    state["documents"] = filtered_docs
    return state


def decide_to_generate(state):
    logger.info("---ASSESS GRADED DOCUMENTS---")
    if not state["documents"]:
        logger.info("---DECISION: NO DOCS => handle_no_answer---")
        return "handle_no_answer"
    else:
        logger.info("---DECISION: proceed to generate---")
        return "generate"


def generate(state):
    logger.info("---GENERATE---")
    question = state["question"]
    documents = state["documents"]

    if not documents:
        # No documents => no answer
        generation = "I'm sorry, but the documents do not contain information about your question."
        state["generation"] = generation
        return state

    # Build the context
    context = "\n\n".join(
        f"[Source {i+1}] {doc.page_content}"
        for i, doc in enumerate(documents)
    )
    sources_str = "\n".join(
        f"[Source {i+1}]: {doc.metadata.get('source', 'N/A')} (Chunk {doc.metadata.get('chunk_index', 'N/A')})"
        for i, doc in enumerate(documents)
    )
    full_context = f"{context}\n\nSources:\n{sources_str}"

    # RAG generation
    generation = rag_chain.invoke({"context": full_context, "question": question})
    state["generation"] = generation
    return state


def grade_generation_v_documents_and_question(state):
    logger.info("---CHECK HALLUCINATIONS---")
    question = state["question"]
    generation = state["generation"]
    documents = state["documents"]

    # Map citations
    source_mapping = map_citations_to_sources(generation, documents)
    state["source_mapping"] = source_mapping  # keep in state

    # Flatten mapped docs for grading
    mapped_docs = list(source_mapping.values())

    # Hallucination check
    hall_score = hallucination_grader.invoke(
        {"documents": format_docs(mapped_docs), "generation": generation}
    )
    hall_grade = hall_score.get("score", None)

    if hall_grade == "yes":
        # Then check if it actually addresses the question
        ans_score = answer_grader.invoke({"question": question, "generation": generation})
        ans_grade = ans_score.get("score", None)
        if ans_grade == "yes":
            logger.info("---DECISION: generation addresses question -> END---")
            # We keep only the mapped_docs
            state["documents"] = mapped_docs
            return "useful"
        else:
            logger.info("---DECISION: does not address question -> no_answer---")
            return "no_answer"
    else:
        logger.info("---DECISION: generation is not grounded -> no_answer---")
        return "no_answer"


def handle_no_answer(state):
    logger.info("---HANDLE NO ANSWER---")
    generation = "I'm sorry, but the documents do not contain information about your question."
    state["generation"] = generation
    return state


# -------------------------------------------
#  Build the Graph
# -------------------------------------------
workflow = StateGraph(GraphState)

# (Optional) If you want to transform the question first:
# workflow.add_node("transform_query", transform_query)
# workflow.add_edge(START, "transform_query")
# workflow.add_edge("transform_query", "retrieve")

# For now, go directly from START -> retrieve
workflow.add_node("retrieve", retrieve)
workflow.add_edge(START, "retrieve")

workflow.add_node("grade_documents", grade_documents)
workflow.add_edge("retrieve", "grade_documents")

workflow.add_node("generate", generate)
workflow.add_node("handle_no_answer", handle_no_answer)

workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "handle_no_answer": "handle_no_answer",
        "generate": "generate",
    },
)
workflow.add_edge("handle_no_answer", END)

workflow.add_conditional_edges(
    "generate",
    grade_generation_v_documents_and_question,
    {
        "useful": END,
        "no_answer": "handle_no_answer",
    },
)

app = workflow.compile()
