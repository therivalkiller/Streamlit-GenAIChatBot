"""
Chat logic and LLM interaction
"""
import streamlit as st
from langchain_groq import ChatGroq
from database import save_message_in_db, now_iso

def process_user_message(user_prompt, current_id, current_meta, selected_model):
    """Process user input and generate AI response"""
    # Display user message
    st.chat_message("user").markdown(user_prompt)
    
    # Save user message to database
    save_message_in_db(current_id, "user", user_prompt, selected_model)
    seq = len(current_meta["messages"]) + 1
    current_meta["messages"].append({
        "role": "user", 
        "content": user_prompt, 
        "created_at": now_iso(), 
        "seq": seq,
        "model_id": selected_model
    })
    
    # Prepare messages for LLM
    messages_for_llm = [{"role": "system", "content": "You're a helpful assistant."}] + [
        {"role": m["role"], "content": m["content"]} for m in current_meta["messages"]
    ]
    
    # Initialize LLM with selected model
    llm = ChatGroq(
        model=selected_model,
        temperature=0.1,
    )
    
    # Generate response
    with st.spinner("Thinking..."):
        response = llm.invoke(input=messages_for_llm)
    assistant_response = response.content
    
    # Display assistant response
    with st.chat_message("assistant"):
        st.markdown(assistant_response)
        st.caption(f"_via {selected_model}_")
    
    # Save assistant message to database
    save_message_in_db(current_id, "assistant", assistant_response, selected_model)
    seq = len(current_meta["messages"]) + 1
    current_meta["messages"].append({
        "role": "assistant", 
        "content": assistant_response, 
        "created_at": now_iso(), 
        "seq": seq,
        "model_id": selected_model
    })