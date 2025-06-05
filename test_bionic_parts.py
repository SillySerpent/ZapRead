from app.bionic.processors.utils import get_bionic_word_parts

test_text = 'Hello world, this is a test of bionic reading functionality.'
print('Testing get_bionic_word_parts...')
parts = get_bionic_word_parts(test_text, intensity=0.4)
print(f'Parts: {parts}')
print(f'Has bold parts: {any(is_bold for _, is_bold in parts)}')

# Test individual words
words = ['Hello', 'world', 'functionality']
for word in words:
    word_parts = get_bionic_word_parts(word, intensity=0.4)
    print(f'Word "{word}": {word_parts}') 