import pypdf
import sys

def extract_text(pdf_path):
    try:
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    pdf_path = r"c:\Users\ibnou\DataGovProjetFederateur\docs\Cahier_des_Charges_Projet_Fédérateur.pdf"
    print(extract_text(pdf_path))
