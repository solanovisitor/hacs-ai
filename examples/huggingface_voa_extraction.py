#!/usr/bin/env python3
"""
Hugging Face VOA-Alpaca Dataset Extraction Pipeline

This example demonstrates extracting HACS resources from the voa-engines/voa-alpaca
dataset, which contains Portuguese medical transcriptions and clinical contexts.

The pipeline:
1. Loads the dataset from Hugging Face
2. Parses content within [TRANSCRIÇÃO] and [CONTEXTO] tags
3. Extracts all possible HACS resources using citation-guided extraction
4. Displays results with Portuguese clinical data

Requirements:
- HUGGINGFACE_API_TOKEN in .env file
- OPENAI_API_KEY in .env file (for LLM extraction)
"""

import asyncio
import os
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def extract_content_from_tags(text: str) -> Dict[str, str]:
    """
    Extract content from [TRANSCRIÇÃO] and [CONTEXTO] tags.
    
    Args:
        text: Raw input text containing tagged content
        
    Returns:
        Dictionary with extracted content
    """
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

async def load_voa_dataset(num_entries: int = 10) -> List[Dict[str, Any]]:
    """
    Load the VOA-Alpaca dataset from Hugging Face.
    
    Args:
        num_entries: Number of entries to load
        
    Returns:
        List of dataset entries
    """
    try:
        from datasets import load_dataset
        
        print(f"📥 Loading {num_entries} entries from voa-engines/voa-alpaca...")
        
        # Load dataset
        dataset = load_dataset("voa-engines/voa-alpaca", split="train")
        
        # Take first num_entries
        entries = []
        for i, item in enumerate(dataset):
            if i >= num_entries:
                break
                
            # Extract content from tags
            if 'input' in item:
                parsed_content = extract_content_from_tags(item['input'])
                entries.append({
                    'id': i,
                    'original_input': item['input'],
                    'parsed_content': parsed_content,
                    'instruction': item.get('instruction', ''),
                    'output': item.get('output', '')
                })
        
        print(f"✅ Loaded {len(entries)} entries successfully")
        return entries
        
    except ImportError:
        print("❌ datasets library not installed. Install with: pip install datasets")
        return []
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return []

async def extract_resources_from_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract HACS resources from a single dataset entry.
    
    Args:
        entry: Dataset entry with parsed content
        
    Returns:
        Extraction results
    """
    from hacs_utils.extraction import extract_hacs_document_with_citation_guidance
    from hacs_utils import create_llm
    
    # Determine the text to extract from
    parsed = entry['parsed_content']
    
    if 'transcricao' in parsed:
        source_text = f"Transcrição médica: {parsed['transcricao']}"
        content_type = "transcricao"
    elif 'contexto' in parsed:
        source_text = f"Contexto clínico: {parsed['contexto']}"  
        content_type = "contexto"
    elif 'raw_text' in parsed:
        source_text = parsed['raw_text']
        content_type = "raw_text"
    else:
        return {
            'entry_id': entry['id'],
            'error': 'No extractable content found',
            'resources': []
        }
    
    try:
        # Create LLM provider
        llm = create_llm("gpt-4o-mini")
        
        print(f"🔍 Extracting from entry {entry['id']} ({content_type})...")
        
        # Extract resources using citation-guided approach
        results = await extract_hacs_document_with_citation_guidance(
            llm_provider=llm,
            source_text=source_text,
            max_concurrency=2,  # Reduced for rate limiting
            timeout_seconds=30
        )
        
        # Count resources by type
        resource_counts = {}
        total_resources = 0
        
        for resource_type, resources in results.items():
            if resources:
                count = len(resources)
                resource_counts[resource_type] = count
                total_resources += count
        
        return {
            'entry_id': entry['id'],
            'content_type': content_type,
            'source_length': len(source_text),
            'total_resources': total_resources,
            'resource_counts': resource_counts,
            'resources': results,
            'error': None
        }
        
    except Exception as e:
        return {
            'entry_id': entry['id'],
            'error': str(e),
            'resources': []
        }

async def run_voa_extraction_pipeline():
    """Run the complete VOA dataset extraction pipeline."""
    
    print("🚀 VOA-Alpaca HACS Resource Extraction Pipeline")
    print("=" * 60)
    print()
    
    # Check API keys
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found in .env file")
        return
    
    # Load dataset
    entries = await load_voa_dataset(num_entries=10)
    if not entries:
        print("❌ Failed to load dataset entries")
        return
    
    print()
    print("📋 Dataset Preview:")
    for i, entry in enumerate(entries[:3]):
        parsed = entry['parsed_content']
        content_types = list(parsed.keys())
        print(f"   Entry {i}: {content_types}")
        
        # Show snippet of content
        for content_type, content in parsed.items():
            if content_type != 'raw_text':
                snippet = content[:100].replace('\n', ' ')
                print(f"     {content_type}: {snippet}...")
    
    print()
    print("🔬 Starting Resource Extraction...")
    print("-" * 40)
    
    # Extract resources from each entry
    extraction_results = []
    successful_extractions = 0
    total_resources_extracted = 0
    
    for entry in entries:
        result = await extract_resources_from_entry(entry)
        extraction_results.append(result)
        
        if result['error']:
            print(f"❌ Entry {result['entry_id']}: {result['error']}")
        else:
            successful_extractions += 1
            total_resources_extracted += result['total_resources']
            
            print(f"✅ Entry {result['entry_id']} ({result['content_type']}): "
                  f"{result['total_resources']} resources")
            
            # Show resource breakdown
            if result['resource_counts']:
                for resource_type, count in result['resource_counts'].items():
                    print(f"   - {resource_type}: {count}")
    
    print()
    print("📊 Extraction Summary:")
    print(f"   📥 Entries processed: {len(entries)}")
    print(f"   ✅ Successful extractions: {successful_extractions}")
    print(f"   🏥 Total resources extracted: {total_resources_extracted}")
    print(f"   📈 Average resources per entry: {total_resources_extracted/max(successful_extractions, 1):.1f}")
    
    # Aggregate resource type statistics
    print()
    print("🏥 Resource Type Distribution:")
    all_resource_counts = {}
    for result in extraction_results:
        if not result['error'] and result['resource_counts']:
            for resource_type, count in result['resource_counts'].items():
                all_resource_counts[resource_type] = all_resource_counts.get(resource_type, 0) + count
    
    for resource_type, total_count in sorted(all_resource_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {resource_type}: {total_count} total")
    
    # Show detailed results for first successful extraction
    print()
    print("🔍 Detailed Example (First Successful Extraction):")
    print("-" * 50)
    
    for result in extraction_results:
        if not result['error'] and result['total_resources'] > 0:
            print(f"Entry {result['entry_id']} ({result['content_type']}):")
            
            for resource_type, resources in result['resources'].items():
                if resources:
                    print(f"\n📋 {resource_type} ({len(resources)} found):")
                    
                    for i, resource in enumerate(resources[:2]):  # Show first 2 of each type
                        print(f"   Resource {i+1}:")
                        
                        # Show key fields based on resource type
                        if hasattr(resource, 'to_markdown'):
                            # Use to_markdown if available
                            markdown = resource.to_markdown()
                            lines = markdown.split('\n')[:5]  # First 5 lines
                            for line in lines:
                                if line.strip():
                                    print(f"     {line}")
                        else:
                            # Fallback to key attributes
                            if hasattr(resource, 'display_name'):
                                print(f"     Display: {resource.display_name}")
                            if hasattr(resource, 'status'):
                                print(f"     Status: {resource.status}")
                            if hasattr(resource, 'code') and resource.code:
                                print(f"     Code: {resource.code}")
                        
                        # Show citation if available
                        if hasattr(resource, 'agent_meta') and resource.agent_meta:
                            if hasattr(resource.agent_meta, 'citation_span'):
                                span = resource.agent_meta.citation_span
                                if span:
                                    print(f"     Citation: chars {span.start}-{span.end}")
                    
                    if len(resources) > 2:
                        print(f"     ... and {len(resources) - 2} more")
            
            break
    
    print()
    print("🎉 VOA-Alpaca extraction pipeline completed!")

if __name__ == "__main__":
    # Run the pipeline
    asyncio.run(run_voa_extraction_pipeline())
