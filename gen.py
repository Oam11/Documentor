import os
import zipfile
import tempfile
import streamlit as st
from groq import Groq
import ast

# Load the API key from secrets.toml
api_key = st.secrets["groq_api"]["api_key"]
client = Groq(api_key=api_key)

# Set up the Streamlit app
st.title("AI Code Documentation and Data Flow Generator")
st.markdown("Upload a ZIP file containing your Python code to generate comprehensive documentation and visualize data flow.")

# Upload ZIP file
uploaded_file = st.file_uploader("Upload a ZIP file containing your code", type="zip")

if uploaded_file is not None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Extract the ZIP file to a temporary directory
        zip_path = os.path.join(tmp_dir, "uploaded_code.zip")
        with open(zip_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Use zipfile to open and extract the contents of the ZIP file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmp_dir)

        # List all Python files in the extracted folder, including subdirectories
        python_files = []
        for root, dirs, files in os.walk(tmp_dir):
            for file in files:
                if file.endswith('.py'):
                    # Add the relative path of the Python file to the list
                    python_files.append(os.path.relpath(os.path.join(root, file), tmp_dir))

        # Check if there are Python files to select
        if python_files:
            main_file = st.selectbox("Select the main file", python_files)

            # Ensure that a main file is selected
            if main_file:
                # Read the content of the main file
                main_file_path = os.path.join(tmp_dir, main_file)
                with open(main_file_path, 'r') as code_file:
                    code_content = code_file.read()

                # Generate Data Flow Chart using AST
                tree = ast.parse(code_content)

                # Create a list of nodes and edges for the flowchart
                nodes = ['Global']  # Add Global as the starting point
                edges = []
                node_ids = {'Global': 0}

                def add_node(node_name):
                    if node_name not in node_ids:
                        node_ids[node_name] = len(nodes)
                        nodes.append(node_name)

                # Identify function and variable assignments, then add them to the graph
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):  # Detect function definitions
                        add_node(node.name)
                        for n in node.body:
                            if isinstance(n, ast.Assign):  # Detect variable assignments
                                for target in n.targets:
                                    if isinstance(target, ast.Name):
                                        add_node(target.id)
                                        edges.append((node.name, target.id))

                    if isinstance(node, ast.Assign):  # Detect variable assignments outside functions
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                add_node(target.id)
                                edges.append(("Global", target.id))  # Add connection to Global node

                # Create Graphviz DOT format code for the flowchart
                # Adjust size directly in the Graphviz DOT format code
                graphviz_code = "digraph G {\n"
                graphviz_code += '    size="8,6";\n'  # Adjust size as needed
                for node in nodes:
                    graphviz_code += f'    "{node}" [shape=box];\n'
                for edge in edges:
                    graphviz_code += f'    "{edge[0]}" -> "{edge[1]}";\n'
                graphviz_code += "}\n"
                
                # Render the Data Flow Chart
                st.subheader("Data Flow Chart")
                st.graphviz_chart(graphviz_code)

                # Custom prompt for Groq documentation generation
                custom_prompt = (
                    '''Objective:
Generate detailed and structured documentation for Python code. The documentation should enhance code understanding and usability, targeting developers and end-users. It must include the following elements:

Documentation Requirements:
Function/Module Description
Provide a detailed overview of the function or module, explaining its purpose, goals, and significance.
Example:
"[Function/Module Name] is designed to [achieve specific tasks or solve problems]. It simplifies [key processes] and aims to provide an efficient, reliable, and user-friendly solution for [target domain or audience]."

Main Features
Highlight the key features or capabilities:

Core functionalities.
Advanced or unique features.
Benefits or enhancements over alternatives.
Parameters
List and describe all parameters:

Name: Parameter name.
Type: Data type.
Purpose: What it does and why it’s needed.
Attributes (for classes)
Document all class attributes:

Name: Attribute name.
Type: Data type.
Purpose: Why it exists and how it is used.
Methods (for classes)
List and document each method, including:

Purpose of the method.
Parameters.
Return type.
Exceptions (if any).
Returns
Specify the return type and explain the value returned:

What the return value represents.
Why it’s significant.
Example Usage
Provide clear and concise examples of how the function or class is used:

Input format.
Expected output.
Use cases for practical scenarios.
Inherited Members (for classes)
Include any inherited attributes or methods:

Explain how inherited components enhance functionality.
List relevant parent classes.
Side Effects
Highlight any side effects of the code:

Changes to external states (e.g., file systems, global variables).
Impacts on performance or environment.
Inline and Function Comments
Ensure the code itself is well-documented with:

Inline Comments: Explain complex logic, critical decisions, or non-obvious operations.
Function Comments: At the start of each function, summarize its purpose, assumptions, and considerations.
Class Documentation (if applicable)
For any class, include:

Purpose: What the class represents.
Attributes: Detailed list of class variables.
Methods: Overview of methods with brief descriptions.
Usage Example: Show how to create and use the class.
Guidelines for Generated Documentation:
Follow Python docstring conventions (PEP 257).
Ensure clarity and readability.
Include practical insights to assist users in leveraging the code effectively.'''
                )

                # Call Groq API to generate documentation
                try:
                    response = client.chat.completions.create(
                        messages=[{"role": "user", "content": f"{custom_prompt}\n\n{code_content}"}],
                        model="llama-3.2-1b-preview"  # Ensure you're using the correct model version
                    )
                    st.success("Documentation Generated Successfully!")
                    doc_content = response.choices[0].message.content
                    st.write(doc_content)

                    # Add a download button for the Markdown file
                    md_filename = "generated_documentation.md"
                    st.download_button(
                        label="Download Documentation as MD",
                        data=doc_content,
                        file_name=md_filename,
                        mime="text/markdown"
                    )

                except Exception as e:
                    st.error(f"An error occurred while generating documentation: {str(e)}")

        else:
            st.warning("No Python files found in the uploaded ZIP file.")
else:
    st.info("Please upload a ZIP file to proceed.")
