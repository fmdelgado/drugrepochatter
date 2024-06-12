

# DrugRepoChatter: AI-Powered Assistant for Academic Research in Drug Discovery


## Introduction
The challenge of keeping pace with the exponential growth of scientific literature is a significant obstacle in drug discovery research. To address this challenge, we have developed DrugRepoChatter, an AI-powered assistant designed to facilitate efficient and accurate information retrieval within a large corpus of scientific documents.

## Description
DrugRepoChatter aims to assist researchers in finding relevant information within a large corpus of scientific documents. By leveraging advanced AI techniques, it provides researchers with a streamlined method to search and access scientific literature relevant to their work, improving the efficiency and effectiveness of the research process.

## Configuration
To configure the knowledge base, navigate to the "Configure Knowledge Base" page. Here, you can upload PDFs which will be used to form the new knowledge base. You can also select an existing knowledge base or delete one.

**Note**: A few knowledge bases are protected and cannot be deleted.

## Requirements

- Streamlit for the frontend interface.
- Docker for containerization.

## Installation
1. **Clone the Repository**:
    ```bash
    git clone https://github.com/fmdelgado/drugrepochat.git
    cd drugrepochat
    ```

2. **Prepare the Environment File**:
    - Use the provided `env_prod` file, rename it to `.env`, and place it in the app directory.

3. **Build and Run the Docker Containers**:
    ```bash
    docker-compose up --build -d
    ```

**Note**: In the terminal where you ran the docker-compose command, some logs may occur, but they shouldn’t be of your concern as long as the application is running properly. In the beginning, you might have to wait a bit until everything has loaded.

## Running the Application
1. Open your browser and navigate to `http://localhost:8501`. The application should be running and accessible from this URL.

## Acknowledgements
**Availability of supporting data**: manuscript in preparation

**Code availability**: [DrugRepoChatter GitHub Repository](https://github.com/fmdelgado/drugrepochatter)

**Competing interests**: The authors declare no conflicts of interest.

**Funding**: This work is supported by the European Union’s Horizon Europe research and innovation programme under grant agreement No. 101057619.

## Additional Information
**Troubleshooting**:
- Ensure Docker is installed and running on your machine.
- Verify that the `.env` file is correctly placed and configured.
- If you encounter issues, check the Docker logs for more details.

**Contact**:
For further information or support, please reach out to the project maintainers through the GitHub repository.
