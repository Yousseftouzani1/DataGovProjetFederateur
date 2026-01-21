import pypdf
import os

def extract_content(pdf_path, output_dir):
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        reader = pypdf.PdfReader(pdf_path)
        full_text = ""
        
        print(f"Extracting content from {len(reader.pages)} pages...")
        
        for i, page in enumerate(reader.pages):
            # Extract text
            text = page.extract_text()
            if text:
                full_text += f"\n--- Page {i+1} ---\n{text}\n"
            
            # Extract images
            for j, image in enumerate(page.images):
                image_name = f"page_{i+1}_img_{j+1}_{image.name}"
                image_path = os.path.join(output_dir, image_name)
                with open(image_path, "wb") as fp:
                    fp.write(image.data)
                print(f"Saved image: {image_name}")

        return full_text
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    pdf_path = r"c:\Users\ibnou\DataGovProjetFederateur\docs\Cahier_des_Charges_Projet_Fédérateur.pdf"
    output_dir = r"c:\Users\ibnou\DataGovProjetFederateur\docs\extracted_content"
    
    text = extract_content(pdf_path, output_dir)
    
    # Save text to file
    with open(os.path.join(output_dir, "extracted_text.txt"), "w", encoding="utf-8") as f:
        f.write(text)
        
    print("Extraction complete. Text saved to extracted_text.txt")
