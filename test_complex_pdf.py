import fitz
from app.bionic.processors.pdf_advanced import AdvancedPDFProcessor
from app.bionic.core.bionic_config import BionicConfiguration

# Create a more complex test PDF with multiple paragraphs
doc = fitz.open()
page = doc.new_page()

# Add multiple lines of text at different positions
texts = [
    'This is the first paragraph of our bionic reading test.',
    'Here we have a second paragraph with longer words like functionality.',
    'The third paragraph tests complex vocabulary and terminology.',
    'Finally, we check readability and comprehension improvements.'
]

y_pos = 100
for text in texts:
    page.insert_text((50, y_pos), text, fontsize=11, fontname='helv')
    y_pos += 30

doc.save('test_complex.pdf')
doc.close()

# Process with the main process method
config = BionicConfiguration()
processor = AdvancedPDFProcessor(config)

print('Testing complex PDF processing...')
result = processor.process('test_complex.pdf', config, output_path='test_complex_output.pdf')
print(f'Result: {result}')
print('Complex test PDF created: test_complex_output.pdf') 