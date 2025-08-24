#!/usr/bin/env python3
"""
Test script for VOA dataset parsing functionality.

This script tests the tag extraction logic without requiring the full dataset.
"""

import re
from typing import Dict

def extract_content_from_tags(text: str) -> Dict[str, str]:
    """Extract content from [TRANSCRIÇÃO] and [CONTEXTO] tags."""
    content = {}
    
    # Extract TRANSCRIÇÃO content (only the content between tags)
    transcricao_pattern = r'\[TRANSCRIÇÃO\]\s*(.*?)\s*\[/TRANSCRIÇÃO\]'
    transcricao_match = re.search(transcricao_pattern, text, re.DOTALL | re.IGNORECASE)
    if transcricao_match:
        extracted = transcricao_match.group(1).strip()
        # Remove any instruction text that might be included
        if extracted and not extracted.startswith('É a transcrição'):
            content['transcricao'] = extracted
    
    # Extract CONTEXTO content (only the content between tags)
    contexto_pattern = r'\[CONTEXTO\]\s*(.*?)\s*\[/CONTEXTO\]'
    contexto_match = re.search(contexto_pattern, text, re.DOTALL | re.IGNORECASE)
    if contexto_match:
        extracted = contexto_match.group(1).strip()
        # Remove any instruction text that might be included
        if extracted and not extracted.startswith('é uma anamnese'):
            content['contexto'] = extracted
    
    # If no tags found, use the whole text as context
    if not content:
        content['raw_text'] = text.strip()
    
    return content

def test_parsing():
    """Test the parsing with sample data."""
    
    # Test case 1: TRANSCRIÇÃO tag
    sample1 = """
- Retorne somente os campos que possuem informações em [TRANSCRIÇÃO] para serem preenchidos.
- [TRANSCRIÇÃO]: É a transcrição de áudio da consulta médica.

[TRANSCRIÇÃO]
Para insônia eu não tenho um laudo, mas é uma coisa que já desde a pandemia que eu apresento uma insônia assim que se repete e eu tô tomando várias coisas assim para me ajudar a dormir né já tentei melatonina melatonina não funciona mais para mim não é causado por baixa produção de melatonina não importa ...
[/TRANSCRIÇÃO]
"""

    # Test case 2: CONTEXTO tag  
    sample2 = """
[CONTEXTO] é uma anamnese de um atendimento de saúde.
Aqui está o contexto:
[CONTEXTO]
Identificação:
--------------

* Nome: Joelma Gomes Henriques Queiroz
* Idade: 55 anos

Evolução Clínica:
-----------------

Paciente relata alteração recente na medicação psiquiátrica devido à sensação de prostração associada ao uso prévio de Rivotril.
[/CONTEXTO]
"""

    # Test case 3: Both tags
    sample3 = """
[TRANSCRIÇÃO]
Boa tarde. Oi doutor, tudo bem? Tudo bem, como posso ajudar a dona Janaína?
[/TRANSCRIÇÃO]

[CONTEXTO]
Paciente do sexo feminino, 45 anos, com queixa de dor abdominal.
[/CONTEXTO]
"""

    print("🧪 Testing VOA Dataset Parsing")
    print("=" * 40)
    
    test_cases = [
        ("TRANSCRIÇÃO only", sample1),
        ("CONTEXTO only", sample2), 
        ("Both tags", sample3)
    ]
    
    for name, sample in test_cases:
        print(f"\n📝 Test: {name}")
        result = extract_content_from_tags(sample)
        
        for content_type, content in result.items():
            print(f"   {content_type}: {len(content)} chars")
            # Show first 100 chars
            preview = content[:100].replace('\n', ' ')
            print(f"   Preview: {preview}...")
    
    print("\n✅ Parsing tests completed!")

if __name__ == "__main__":
    test_parsing()
