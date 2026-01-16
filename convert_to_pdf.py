import markdown
from weasyprint import HTML
import os

# Chemins
markdown_file = r"C:\Users\ibnou\.gemini\antigravity\brain\fa424bd2-c38a-4101-95a2-bb5689e72946\livrable_projet_simple.md"
pdf_file = r"C:\Users\ibnou\.gemini\antigravity\brain\fa424bd2-c38a-4101-95a2-bb5689e72946\livrable_projet.pdf"

# Lire le fichier markdown
with open(markdown_file, 'r', encoding='utf-8') as f:
    markdown_content = f.read()

# Convertir markdown en HTML
html_content = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code'])

# Template HTML avec style
html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        @page {{
            size: A4;
            margin: 2cm;
        }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 100%;
        }}
        h1 {{
            color: #2563eb;
            border-bottom: 3px solid #2563eb;
            padding-bottom: 10px;
            margin-top: 30px;
        }}
        h2 {{
            color: #4f46e5;
            margin-top: 25px;
            border-left: 4px solid #4f46e5;
            padding-left: 10px;
        }}
        h3 {{
            color: #6366f1;
            margin-top: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #4f46e5;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f9fafb;
        }}
        code {{
            background-color: #f3f4f6;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        pre {{
            background-color: #1f2937;
            color: #f9fafb;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        pre code {{
            background-color: transparent;
            color: #f9fafb;
        }}
        hr {{
            border: none;
            border-top: 2px solid #e5e7eb;
            margin: 30px 0;
        }}
        ul, ol {{
            margin: 15px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 8px 0;
        }}
        blockquote {{
            border-left: 4px solid #fbbf24;
            background-color: #fffbeb;
            padding: 10px 20px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>
"""

# Convertir HTML en PDF
HTML(string=html_template).write_pdf(pdf_file)

print(f"✅ PDF créé avec succès : {pdf_file}")
