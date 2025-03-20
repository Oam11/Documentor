import os
import zipfile
import tempfile
import streamlit as st
from groq import Groq

# Load the API key from secrets.toml
api_key = st.secrets["groq_api"]["api_key"]
client = Groq(api_key=api_key)

# Set up the Streamlit app
st.title("AI Code Documentation and Data Flow Generator")
st.markdown("Upload a ZIP file containing your code to generate comprehensive documentation for each file.")

# Upload ZIP file
uploaded_file = st.file_uploader("Upload a ZIP file containing your code", type="zip")

if uploaded_file is not None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Extract the ZIP file to a temporary directory
        zip_path = os.path.join(tmp_dir, "uploaded_code.zip")
        with open(zip_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmp_dir)

        # List all files in the extracted folder, including subdirectories
        all_files = []
        for root, dirs, files in os.walk(tmp_dir):
            for file in files:
                all_files.append(os.path.relpath(os.path.join(root, file), tmp_dir))

        if all_files:
            # Initialize combined documentation
            combined_doc = ""

            # Define the old prompt
            custom_prompt = '''
Objective:
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
Include practical insights to assist users in leveraging the code effectively.
'''

            for file in all_files:
                file_path = os.path.join(tmp_dir, file)
                _, file_extension = os.path.splitext(file)

                # Read file content
                with open(file_path, 'r', encoding="utf-8", errors="ignore") as f:
                    file_content = f.read()

                # Combine the custom prompt with the file content
                full_prompt = f"{custom_prompt}\n\n{file_content}"

                try:
                    response = client.chat.completions.create(
                        messages=[{"role": "user", "content": full_prompt}],
                        model="llama-3.3-70b-versatile"
                    )
                    doc_content = response.choices[0].message.content

                    # Append to combined documentation
                    combined_doc += f"# Documentation for {file}\n\n{doc_content}\n\n"

                    st.success(f"Documentation generated for {file}!")

                except Exception as e:
                    st.error(f"An error occurred with {file}: {str(e)}")

            # Provide combined documentation for download
            if combined_doc:
                combined_md_filename = "combined_documentation.md"
                st.download_button(
                    label="Download Combined Documentation",
                    data=combined_doc,
                    file_name=combined_md_filename,
                    mime="text/markdown"
                )
        else:
            st.warning("No files found in the uploaded ZIP.")
else:
    st.info("Please upload a ZIP file to proceed.")
