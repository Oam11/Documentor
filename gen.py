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
'''Generate detailed documentation for the following code in English. The documentation should include the following elements:

1. Inline Comments
Provide clear and concise comments throughout the code.
Explain the purpose and logic of each line or block.
Highlight important considerations, such as performance implications, edge cases, or assumptions.
2. Function Documentation
For each function in the code, include:

Description: A concise explanation of what the function does.
Parameters:
List each parameter, specifying its name, type, and purpose.
Return Type:
Specify the return type and describe what the returned value represents.
Exceptions:
Mention any exceptions that the function might raise, including the conditions that trigger them.
Side Effects:
Note any changes the function makes to external states, like modifying global variables or I/O operations.
Example Usage:
Provide sample code demonstrating how to use the function, including expected input and output.
3. Class Documentation (if applicable)
For each class in the code, include:

Description: Briefly describe the class and its purpose.
Attributes:
Document each class attribute, specifying its type and purpose.
Methods:
List and document all methods within the class, following the function documentation format.
Example Usage:
Show how to instantiate and use the class.
4. Module-Level Documentation
Provide an overview of the module’s purpose and functionality.
Highlight how different functions, classes, or components within the module interact.
5. Best Practices and Optimization Notes
Include tips for using the code efficiently.
Mention any known limitations or potential improvements.
6. Testing Information
Outline how the code can be tested.
Mention any test cases or frameworks used, and provide examples if possible.
7. Additional Notes
Include any relevant information that enhances understanding, such as dependencies, related modules, or design decisions.'''
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
