import os
import streamlit as st
from groq import Groq
import zipfile
import tempfile

# Load the API key from secrets.toml
api_key = st.secrets["groq_api"]["api_key"]
client = Groq(api_key=api_key)

st.title("AI Code Documentation System")

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

        # List all the Python files in the extracted folder, including subdirectories
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

                # Input for custom prompt
                custom_prompt =(
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
                        messages=[{"role": "user", "content": f"{custom_prompt}\n{code_content}"}],
                        model="llama-3.2-1b-preview"  # Ensure you're using the correct model version
                    )
                    st.success("Documentation Generated Successfully!")
                    st.write(response.choices[0].message.content)

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("No Python files found in the uploaded ZIP file.")
