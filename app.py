from flask import Flask, render_template, request, jsonify, Response
from rag_phi3 import RAGChain
import json
import random

app = Flask(__name__)

# Initialize RAG chain with default model (lowercase to match available models)
rag_chain = RAGChain(model_name="phi")

# Available models
AVAILABLE_MODELS = ["phi", "smol", "gemma"]

@app.route('/')
def index():
    return render_template('index.html', models=AVAILABLE_MODELS, current_model=rag_chain.model_name)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    query = data.get('query', '').strip()
    model = data.get('model', rag_chain.model_name)
    stream = data.get('stream', True)  # Default to streaming
    
    if not query:
        return jsonify({'error': 'Query cannot be empty'}), 400
    
    # Switch model if different from current
    if model != rag_chain.model_name:
        rag_chain.switch_model(model)
    
    if stream:
        # Return streaming response
        def generate():
            try:
                # Get response from RAG chain
                retrieved_docs = rag_chain.retrieve(query, top_k=2)
                context = "\n".join(retrieved_docs)
                prompt = f"Use the following context to answer the question concisely. Context: {context} \n Question: {query} \nAnswer:"
                
                # Stream response
                try:
                    chunk_count = 0
                    for chunk in rag_chain.ollama.stream(prompt):
                        chunk_count += 1
                        # Handle different chunk formats (string or dict)
                        if isinstance(chunk, dict):
                            # Extract text from dict if it's a langchain format
                            chunk_text = chunk.get('content', chunk.get('text', str(chunk)))
                        else:
                            chunk_text = str(chunk)
                        
                        if chunk_text:
                            # Send each chunk as JSON
                            yield f"data: {json.dumps({'chunk': chunk_text, 'done': False})}\n\n"
                    
                    if chunk_count == 0:
                        # No chunks received, fallback to non-streaming
                        print("No chunks received from stream, using invoke instead")
                        response = rag_chain.ollama.invoke(prompt)
                        yield f"data: {json.dumps({'chunk': str(response), 'done': False})}\n\n"
                except (AttributeError, TypeError) as e:
                    # Fallback if streaming not supported
                    print(f"Streaming error: {e}, falling back to non-streaming")
                    response = rag_chain.ollama.invoke(prompt)
                    yield f"data: {json.dumps({'chunk': str(response), 'done': False})}\n\n"
                
                # Send final message with model info
                yield f"data: {json.dumps({'chunk': '', 'done': True, 'model': rag_chain.model_name})}\n\n"
            except Exception as e:
                import traceback
                error_msg = f"{str(e)}\n{traceback.format_exc()}"
                print(f"Error in generate(): {error_msg}")
                yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
        
        response = Response(generate(), mimetype='text/event-stream')
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['X-Accel-Buffering'] = 'no'
        return response
    else:
        # Non-streaming fallback
        try:
            retrieved_docs = rag_chain.retrieve(query, top_k=2)
            context = "\n".join(retrieved_docs)
            prompt = f"Use the following context to answer the question concisely. Context: {context} \n Question: {query} \nAnswer:"
            
            response = rag_chain.ollama.invoke(prompt)
            
            return jsonify({
                'response': response,
                'model': rag_chain.model_name
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/switch_model', methods=['POST'])
def switch_model():
    data = request.json
    model = data.get('model', 'phi')
    
    if model not in AVAILABLE_MODELS:
        return jsonify({'error': f'Model {model} not available'}), 400
    
    try:
        rag_chain.switch_model(model)
        return jsonify({
            'success': True,
            'model': rag_chain.model_name,
            'message': f'Switched to model: {rag_chain.model_name}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/current_model', methods=['GET'])
def current_model():
    return jsonify({'model': rag_chain.model_name})

@app.route('/quiz')
def quiz():
    return render_template('quiz.html', models=AVAILABLE_MODELS, current_model=rag_chain.model_name)

@app.route('/generate_question', methods=['POST'])
def generate_question():
    data = request.json
    model = data.get('model', rag_chain.model_name)
    topic = data.get('topic', '').strip()
    
    # Switch model if different from current
    if model != rag_chain.model_name:
        rag_chain.switch_model(model)
    
    try:
        # Retrieve relevant course material
        if topic:
            # Use topic to retrieve relevant material
            # Vary top_k slightly for variation (2-4)
            top_k = random.randint(2, 4)
            retrieved_docs = rag_chain.retrieve(topic, top_k=top_k)
        else:
            # Retrieve random material if no topic specified
            # Vary top_k and use different query variations
            top_k = random.randint(2, 4)
            query_variations = [
                "course material",
                "mathematics concepts",
                "key topics",
                "important concepts",
                "learning material"
            ]
            query = random.choice(query_variations)
            retrieved_docs = rag_chain.retrieve(query, top_k=top_k)
        
        context = "\n".join(retrieved_docs)
        
        # Vary question types and styles for diversity
        question_styles = [
            "application-based question",
            "conceptual understanding question",
            "problem-solving question",
            "explanation question",
            "analysis question"
        ]
        question_approaches = [
            "asks students to explain",
            "requires students to calculate",
            "asks students to compare",
            "requires students to apply",
            "asks students to demonstrate understanding of"
        ]
        
        selected_style = random.choice(question_styles)
        selected_approach = random.choice(question_approaches)
        
        # Generate a question based on the context with variation
        prompt = f"""Based on the following course material, generate a single, clear, and specific {selected_style} that {selected_approach} the key concepts.

Course Material:
{context}

Generate a question that:
1. Tests understanding of important concepts from the material
2. Is clear and specific
3. Can be answered in a few sentences
4. Does not include the answer
5. Is different from questions you might have generated before (vary the wording and focus)

Make sure the question is unique and tests a different aspect or uses different wording than typical questions.

Question:"""
        
        # Temporarily increase temperature for more variation in question generation
        # Save original temperature if it exists
        original_temp = getattr(rag_chain.ollama, 'temperature', None)
        
        # Create a temporary Ollama instance with higher temperature for question generation
        from langchain_community.llms import Ollama
        question_model = Ollama(model=rag_chain.model_name, temperature=0.7)  # Higher temperature for variation
        
        response = question_model.invoke(prompt)
        
        return jsonify({
            'question': response.strip(),
            'model': rag_chain.model_name,
            'context': context  # Store context for later evaluation
        })
    except Exception as e:
        import traceback
        print(f"Error generating question: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json
    question = data.get('question', '').strip()
    answer = data.get('answer', '').strip()
    context = data.get('context', '')
    model = data.get('model', rag_chain.model_name)
    
    if not question or not answer:
        return jsonify({'error': 'Question and answer are required'}), 400
    
    # Switch model if different from current
    if model != rag_chain.model_name:
        rag_chain.switch_model(model)
    
    try:
        # Evaluate the answer
        evaluation_prompt = f"""You are a teacher evaluating a student's answer. Based on the course material provided, provide feedback on the student's answer.

Course Material:
{context}

Question: {question}

Student's Answer: {answer}

Provide a brief explanation (2-3 sentences) evaluating the answer. If the answer is incorrect or partially correct, explain what the correct answer should include.
"""
        
        response = rag_chain.ollama.invoke(evaluation_prompt)
        
        # Parse the response - remove "EXPLANATION:" prefix if present
        explanation = response
        if "EXPLANATION:" in response:
            explanation = response.split("EXPLANATION:", 1)[1].strip()
        
        return jsonify({
            'explanation': explanation,
            'model': rag_chain.model_name
        })
    except Exception as e:
        import traceback
        print(f"Error evaluating answer: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

