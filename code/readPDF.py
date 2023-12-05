import os
import openai
import PyPDF2

# Set up OpenAI API key
openai.api_key = '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'

# Function to extract text from PDF using PyPDF2
def extract_text_from_pdf(pdf_path):
    text = ''
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        num_pages = len(pdf_reader.pages)

        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()

    return text

# Function to summarize text using GPT-3
def summarize_with_gpt3(text):
    response = openai.Completion.create(
      engine="text-davinci-003",
      prompt=text,
      max_tokens=100
    )
    return response.choices[0].text.strip()

# Loop through the PDF files in a directory
pdf_folder = '../drafts'
for file_name in os.listdir(pdf_folder):
    if file_name.endswith('.pdf'):
        # Use PyPDF2 or pdfplumber to extract text from the PDF
        # Extract text and store it in 'text'
        pdf_path = os.path.join(pdf_folder, file_name)
        
        # Extract text from the PDF
        extracted_text = extract_text_from_pdf(pdf_path)
        # Call the summarize_with_gpt3 function with the extracted text
        summarized_text = summarize_with_gpt3(extracted_text)

        # Print or save the summarized text
        print(f"Summary of {file_name}:\n{summarized_text}\n")
