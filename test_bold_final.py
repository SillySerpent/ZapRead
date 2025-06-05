import fitz
from app.bionic.processors.pdf_advanced import AdvancedPDFProcessor
from app.bionic.core.bionic_config import BionicConfiguration

# Create test PDF
doc = fitz.open()
page = doc.new_page()
page.insert_text((100, 100), 'Hello world, this is a test of bionic reading functionality.', fontsize=12, fontname='helv')
doc.save('test_bold_final.pdf')
doc.close()

# Process with both methods
config = BionicConfiguration()
processor = AdvancedPDFProcessor(config)

print('Testing both processing methods...')

# Test morphing method
print('\n=== MORPHING METHOD TEST ===')
result1 = processor._process_with_morphing(fitz.open('test_bold_final.pdf'), config, 'test_output_morphing.pdf')
print(f'Morphing result: {result1}')

# Test redaction method  
print('\n=== REDACTION METHOD TEST ===')
result2 = processor._process_with_redaction(fitz.open('test_bold_final.pdf'), config, 'test_output_redaction.pdf')
print(f'Redaction result: {result2}')

print('\nBoth test files created. Check test_output_morphing.pdf and test_output_redaction.pdf') 