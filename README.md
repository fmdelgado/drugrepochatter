# DrugRepoChatter: AI-Powered Assistant for Academic Research in Drug Discovery

<p align="center">
  <img src="https://github.com/fmdelgado/drugrepochatter/blob/main/app/img/logo.png?raw=true" width="200"/>
</p>

## Introduction

The exponential growth of scientific literature presents a significant challenge in drug discovery research. Keeping pace with the latest developments and efficiently extracting relevant information has become increasingly difficult. To address this challenge, we have developed DrugRepoChatter, an AI-powered assistant designed to facilitate efficient and accurate information retrieval within a large corpus of scientific documents.

## Description

DrugRepoChatter is an innovative tool aimed at assisting researchers in navigating and extracting relevant information from a vast collection of scientific literature. By leveraging advanced AI techniques, including large language models and retrieval augmented generation, it provides researchers with a streamlined method to search, access, and synthesize scientific literature relevant to their work. This tool significantly improves the efficiency and effectiveness of the research process in drug discovery and repurposing.

Key features include:
- Natural language querying of scientific literature
- AI-powered responses based on the content of the knowledge base
- Customizable search parameters for fine-tuned results
- Ability to create and manage personal knowledge bases
- Integration with a curated database of drug repurposing literature

## Configuration

To configure the knowledge base:

1. Navigate to the "Configure Knowledge Base" page.
2. Here you can:
   - Upload PDFs to form a new knowledge base
   - Select an existing knowledge base
   - Delete a knowledge base (note: some are protected and cannot be deleted)

The default knowledge base, created by the REPO4EU consortium, contains full-text of 285 carefully curated publications on drug repurposing.

## Requirements

- Streamlit for the frontend interface
- Docker for containerization
- Python 3.8+
- Various Python libraries including LangChain, FAISS, and PyPDF2 (see requirements.txt for full list)

## Installation

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/fmdelgado/drugrepochat.git
    cd drugrepochat
    ```

2. **Prepare the Environment File**:
    - Use the provided `env_prod` file, rename it to `.env`, and place it in the app directory.
    - Ensure all necessary environment variables are correctly set.

3. **Build and Run the Docker Containers**:
    ```bash
    docker-compose up --build -d
    ```

**Note**: Initial startup may take some time as the containers are built and the application is initialized. Some logs may appear in the terminal, which are normal as long as the application starts successfully.

## Running the Application

1. Open your browser and navigate to `http://localhost:8501`.
2. The application should be running and accessible from this URL.
3. Sign up for an account or log in to access all features.
4. Start by selecting or creating a knowledge base, then use the Q&A feature to interact with the AI assistant.

## Usage Tips

- Be specific in your questions to get more accurate responses.
- Experiment with the search parameters (score threshold, k, fetch_k) to fine-tune your results.
- Remember that DrugRepoChatter's knowledge is based on the documents in the selected knowledge base.

## Limitations

- The tool is focused on drug repurposing, omics data, bioinformatics, and data analysis.
- Responses are generated based on the content of the knowledge base, not real-time data.

## Acknowledgements

- **Availability of supporting data**: Manuscript in preparation
- **Code availability**: [DrugRepoChatter GitHub Repository](https://github.com/fmdelgado/drugrepochatter)
- **Competing interests**: The authors declare no conflicts of interest.
- **Funding**: This work is supported by the European Union's Horizon Europe research and innovation programme under grant agreement No. 101057619.

## Additional Information

**Troubleshooting**:
- Ensure Docker is installed and running on your machine.
- Verify that the `.env` file is correctly placed and configured.
- If you encounter issues, check the Docker logs for more details.

**Contact**:
For further information or support, please reach out to the project maintainers through the GitHub repository.

## Future Development

We are continuously working on improving DrugRepoChatter. Future updates may include:
- Expansion of the knowledge base with more recent publications
- Integration with real-time literature databases
- Enhanced natural language processing capabilities
- User feedback integration for continual improvement

Your feedback and contributions are welcome as we strive to make DrugRepoChatter an indispensable tool for drug discovery researchers.