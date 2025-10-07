import fitz 
import re
import logging

logger = logging.getLogger(__name__)

def extract_mcqs_from_pdf(pdf_file, topic="Python", subtopic="Decision Making", difficulty="medium"):
    """
    Extracts MCQs from a PDF and returns them as a list of dictionaries.
    Handles multi-line questions and answers properly.
    """
    
    print(f"📖 extract_mcqs_from_pdf called with: topic='{topic}', subtopic='{subtopic}', difficulty='{difficulty}'")
    
    mcqs = []
    
    try:
        # Read PDF bytes
        pdf_bytes = pdf_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # Get all text from all pages
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
        
        doc.close()
        
        print(f"📄 Extracted text length: {len(full_text)} characters")
        
        # Split text into MCQ blocks using regex
        # Pattern: Q followed by number, dot, space, then content until next Q or end
        mcq_pattern = r'Q(\d+)\.(.+?)(?=Q\d+\.|$)'
        mcq_matches = re.findall(mcq_pattern, full_text, re.DOTALL | re.IGNORECASE)
        
        print(f"🔍 Found {len(mcq_matches)} potential MCQs")
        
        for match in mcq_matches:
            question_no = match[0]
            content = match[1].strip()
            
            try:
                mcq_data = parse_mcq_content(content, question_no, topic, subtopic, difficulty)
                if mcq_data:
                    mcqs.append(mcq_data)
                    print(f"✅ Parsed MCQ {question_no}: '{mcq_data['question'][:50]}...'")
                else:
                    print(f"⚠️ Failed to parse MCQ {question_no}")
            except Exception as e:
                print(f"❌ Error parsing MCQ {question_no}: {str(e)}")
        
        print(f"📊 Total MCQs successfully parsed: {len(mcqs)}")
        
    except Exception as e:
        logger.error(f"Error extracting MCQs from PDF: {str(e)}")
        print(f"💥 PDF extraction failed: {str(e)}")
        raise Exception(f"Failed to extract MCQs from PDF: {str(e)}")
    
    return mcqs

def parse_mcq_content(content, question_no, topic, subtopic, difficulty):
    """
    Parse individual MCQ content to extract question, options, and answer
    """
    try:
        # Remove extra whitespace and normalize
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Extract answer first (it's at the end)
        answer_pattern = r'Answer:\s*([A-Da-d])'
        answer_match = re.search(answer_pattern, content)
        
        if not answer_match:
            print(f"❌ No answer found for Q{question_no}")
            return None
            
        raw_answer = answer_match.group(1).upper()
        answer_map = {"A": "1", "B": "2", "C": "3", "D": "4"}
        correct_answer = answer_map.get(raw_answer, "1")
        
        # Remove the answer part from content to get question + options
        content_without_answer = content[:answer_match.start()].strip()
        
        # Split by options pattern (A), B), C), D))
        parts = re.split(r'\b([A-D])\)\s*', content_without_answer)
        
        if len(parts) < 9:  # Should have: question, A, option1, B, option2, C, option3, D, option4
            print(f"❌ Insufficient parts for Q{question_no}: {len(parts)} parts found")
            return None
        
        # First part is the question
        question = parts[0].strip()
        
        # Extract options
        options = {}
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                option_letter = parts[i]
                option_text = parts[i + 1].strip()
                if option_letter in ['A', 'B', 'C', 'D']:
                    options[option_letter] = option_text
        
        # Validate we have all 4 options
        required_options = ['A', 'B', 'C', 'D']
        if not all(opt in options for opt in required_options):
            print(f"❌ Missing options for Q{question_no}. Found: {list(options.keys())}")
            return None
        
        # Clean up question text
        question = question.replace(f"Q{question_no}.", "").strip()
        if not question:
            print(f"❌ Empty question for Q{question_no}")
            return None
        
        mcq_data = {
            "topic": topic,
            "subtopic": subtopic,
            "difficulty": difficulty,
            "question_no": int(question_no),
            "question": question,
            "option1": options['A'],
            "option2": options['B'],
            "option3": options['C'],
            "option4": options['D'],
            "correct_answer": correct_answer
        }
        
        return mcq_data
        
    except Exception as e:
        print(f"❌ Error parsing MCQ content: {str(e)}")
        return None

def extract_mcqs_from_pdf_simple_fallback(pdf_file, topic="Python", subtopic="Decision Making", difficulty="medium"):
    """
    Simple fallback method for basic PDF formats
    """
    print(f"📖 Using simple fallback parser")
    
    mcqs = []
    
    try:
        # Read PDF bytes
        pdf_bytes = pdf_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        question_no = 1
        answer_map = {"A": "1", "B": "2", "C": "3", "D": "4"}
        
        for page in doc:
            lines = [line.strip() for line in page.get_text().split("\n") if line.strip()]
            
            i = 0
            while i < len(lines):
                try:
                    # Look for question pattern
                    if re.match(r'^Q\d+\.', lines[i]):
                        if i + 5 >= len(lines):
                            break
                        
                        # Extract components
                        question_line = lines[i]
                        
                        # Look ahead for options and answer
                        options = []
                        answer_line = ""
                        
                        j = i + 1
                        while j < len(lines) and len(options) < 4:
                            line = lines[j]
                            if re.match(r'^[A-D]\)', line):
                                options.append(line[2:].strip())  # Remove "A) " part
                            j += 1
                        
                        # Look for answer
                        while j < len(lines):
                            if lines[j].startswith("Answer:"):
                                answer_line = lines[j]
                                break
                            j += 1
                        
                        if len(options) == 4 and answer_line:
                            # Extract answer
                            raw_answer = re.search(r"Answer:\s*([A-Da-d])", answer_line)
                            raw_answer = raw_answer.group(1).upper() if raw_answer else "A"
                            mapped_answer = answer_map.get(raw_answer, "1")
                            
                            # Clean question
                            question = re.sub(r'^Q\d+\.\s*', '', question_line).strip()
                            
                            mcq = {
                                "topic": topic,
                                "subtopic": subtopic,
                                "difficulty": difficulty,
                                "question_no": question_no,
                                "question": question,
                                "option1": options[0],
                                "option2": options[1],
                                "option3": options[2],
                                "option4": options[3],
                                "correct_answer": mapped_answer
                            }
                            
                            mcqs.append(mcq)
                            question_no += 1
                            print(f"✅ Fallback parsed MCQ {question_no-1}")
                            
                            i = j + 1
                        else:
                            i += 1
                    else:
                        i += 1
                        
                except Exception as e:
                    print(f"❌ Fallback error at line {i}: {str(e)}")
                    i += 1
        
        doc.close()
        
    except Exception as e:
        print(f"💥 Fallback parser failed: {str(e)}")
        raise Exception(f"All parsing methods failed: {str(e)}")
    
    return mcqs