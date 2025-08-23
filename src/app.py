#!/usr/bin/env python3

"""
Streamlit app for the TalentScout Hiring Assistant
"""

import os
import streamlit as st
from dotenv import load_dotenv
from src.chatbot.conversation_manager import ConversationManager


# Load environment variables
load_dotenv()


def initialize_session_state():
    """Initialize session state variables"""
    if 'conversation_manager' not in st.session_state:
        st.session_state.conversation_manager = ConversationManager()
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'conversation_ended' not in st.session_state:
        st.session_state.conversation_ended = False
    if 'first_load' not in st.session_state:
        st.session_state.first_load = True


def apply_custom_styling():
    """Apply custom CSS for modern white & blue chat interface"""
    st.markdown("""
    <style>
    /* Force light theme background */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], [class^="stApp"] {
        background-color: #ffffff !important;
        color: #202124 !important;
    }

    /* Sidebar (if shown) */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
    }

    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Chat container styling */
    .chat-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        background: #ffffff;
        margin-bottom: 1rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }

    /* Message styling */
    .chat-message {
        padding: 0.75rem 1rem;
        border-radius: 18px;
        margin-bottom: 0.6rem;
        max-width: 80%;
        word-wrap: break-word;
        line-height: 1.5;
        font-size: 0.95rem;
    }

    .user-message {
        background: #1a73e8;
        color: #ffffff;
        margin-left: auto;
        text-align: right;
        border: 1px solid #1669c1;
    }

    .bot-message {
        background: #f1f8ff;
        color: #202124;
        border: 1px solid #d2e3fc;
    }

    .bot-message strong {
        color: #1a73e8;
    }

    /* Input styling */
    .stChatInput > div {
        background: #ffffff;
        border-radius: 25px;
        border: 2px solid #d2e3fc;
    }

    /* Status indicators */
    .status-indicator {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        margin: 0.5rem 0;
        border: 1px solid #d2e3fc;
        background: #f1f8ff;
        color: #1a73e8;
    }

    .typing-indicator {
        background: #e8f0fe;
        color: #1a73e8;
        animation: pulse 1.5s infinite;
    }

    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.6; }
        100% { opacity: 1; }
    }

    /* Conversation ended styling */
    .conversation-ended {
        text-align: center;
        padding: 2rem;
        background: #e8f0fe;
        border-radius: 12px;
        border: 2px dashed #1a73e8;
        color: #1a73e8;
    }
    </style>
    """, unsafe_allow_html=True)


def display_welcome_screen():
    """Display initial welcome screen before conversation starts"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>🤖 TalentScout Hiring Assistant</h1>
        <p style="font-size: 1.1rem; color: #666; margin-bottom: 2rem;">
            Welcome to our AI-powered initial screening process!
        </p>
        <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
            <h3>📋 What to expect:</h3>
            <ul style="text-align: left; max-width: 400px; margin: 0 auto;">
                <li>Quick information collection (5-7 questions)</li>
                <li>Technical questions based on your skills</li>
                <li>About 10-15 minutes total</li>
            </ul>
        </div>
        <p style="color: #666; font-size: 0.9rem;">
            Type any message below to begin the conversation
        </p>
    </div>
    """, unsafe_allow_html=True)


def display_chat_messages():
    """Display chat messages with improved styling"""
    if st.session_state.messages:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)

        for i, message in enumerate(st.session_state.messages):
            role = message["role"]
            content = message["content"]

            # Format content for better display
            formatted_content = content.replace('\n', '<br>')

            if role == "user":
                st.markdown(
                    f'<div class="chat-message user-message">{formatted_content}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="chat-message bot-message">{formatted_content}</div>',
                    unsafe_allow_html=True
                )

        st.markdown('</div>', unsafe_allow_html=True)


def main():
    # Page configuration
    st.set_page_config(
        page_title="TalentScout Hiring Assistant",
        page_icon="🤖",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    # Apply custom styling
    apply_custom_styling()

    # Initialize session state
    initialize_session_state()

    # Check for API key
    if not os.getenv("OPENROUTER_API_KEY"):
        st.error("❌ OPENROUTER_API_KEY not found in environment variables. Please check your .env file.")
        st.stop()

    # Main app logic
    if not st.session_state.messages and st.session_state.first_load:
        # Show welcome screen for first-time users
        display_welcome_screen()
    else:
        # Show chat interface
        st.title("🤖 TalentScout Hiring Assistant")

        # Display conversation status
        conv_state = st.session_state.conversation_manager.state
        if conv_state == "greeting":
            st.markdown("👋 **Ready to start** - Waiting for your message")
        elif conv_state == "collecting_info":
            current_field = st.session_state.conversation_manager.awaiting_field
            st.markdown(f"📝 **Collecting information** - Current: {current_field or 'personal details'}")
        elif conv_state == "tech_transition":
            st.markdown("⚡ **Preparing technical questions**")
        elif conv_state == "technical_questions":
            q_num = st.session_state.conversation_manager.current_question_index + 1
            total_q = len(st.session_state.conversation_manager.current_questions)
            st.markdown(f"🧠 **Technical assessment** - Question {q_num}/{total_q}")
        elif conv_state == "ended":
            st.markdown("✅ **Assessment completed**")

        # Display chat messages
        display_chat_messages()

    # Handle user input
    if not st.session_state.conversation_ended:
        user_input = st.chat_input("Type your message here...")

        if user_input:
            # Mark as no longer first load
            st.session_state.first_load = False

            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})

            # Show typing indicator
            with st.spinner("Assistant is typing..."):
                # Get bot response
                response, conversation_ended = st.session_state.conversation_manager.process_message(user_input)

            # Add bot response
            st.session_state.messages.append({"role": "assistant", "content": response})

            # Update conversation status
            if conversation_ended:
                st.session_state.conversation_ended = True

            # Rerun to show new messages
            st.rerun()
    else:
        # Conversation ended - show completion message
        st.markdown("""
        <div class="conversation-ended">
            <h3>✅ Assessment Completed!</h3>
            <p>Thank you for completing our initial screening process.</p>
            <p>Your responses have been saved securely.</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Start New Assessment", use_container_width=True):
                # Clear all session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        with col2:
            if st.button("📊 View Summary", use_container_width=True):
                # Show conversation summary
                with st.expander("Conversation Summary", expanded=True):
                    candidate_data = st.session_state.conversation_manager.candidate_data
                    if candidate_data:
                        st.write("**Candidate Information:**")
                        for field, value in candidate_data.items():
                            if field not in ["email", "phone_number", "current_location"]:  # Don't show encrypted fields
                                st.write(f"- **{field.replace('_', ' ').title()}:** {value}")

                        tech_responses = st.session_state.conversation_manager.technical_responses
                        if tech_responses:
                            st.write("\n**Technical Questions Asked:**", len(tech_responses))


if __name__ == "__main__":
    main()
