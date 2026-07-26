# Importing necessary libraries
from openai import OpenAI
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

MAX_QUESTIONS = 5

# Setting up the Streamlit page configuration
st.set_page_config(page_title="Streamlit Chat", page_icon="💬")
st.title("Interview Chatbot")

if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False

if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0

if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False


def complete_setup():
    st.session_state.setup_complete = True


def show_feedback():
    st.session_state.feedback_shown = True


if not st.session_state.setup_complete:

    st.subheader("Personal Information", divider="rainbow")

    if "name" not in st.session_state:
        st.session_state["name"] = ""

    if "experience" not in st.session_state:
        st.session_state["experience"] = ""

    if "skills" not in st.session_state:
        st.session_state["skills"] = ""

    st.session_state["name"] = st.text_input(
        label="Name",
        max_chars=40,
        value=st.session_state["name"],
        placeholder="Enter your name"
    )

    st.session_state["experience"] = st.text_area(
        label="Experience",
        value=st.session_state["experience"],
        height=None,
        max_chars=200,
        placeholder="Describe your experience"
    )

    st.session_state["skills"] = st.text_area(
        label="Skills",
        value=st.session_state["skills"],
        height=None,
        max_chars=200,
        placeholder="List your skills"
    )

    st.subheader("Company and Position", divider="rainbow")

    if "level" not in st.session_state:
        st.session_state["level"] = "Junior"

    if "position" not in st.session_state:
        st.session_state["position"] = "Data Scientist"

    if "company" not in st.session_state:
        st.session_state["company"] = "Amazon"

    col1, col2 = st.columns(2)

    with col1:
        st.session_state["level"] = st.radio(
            "Choose level",
            key="visibility",
            options=["Junior", "Mid-Level", "Senior"]
        )

    with col2:
        st.session_state["position"] = st.selectbox(
            "Choose a position",
            (
                "Data Scientist",
                "Data Engineer",
                "ML Engineer",
                "BI Analyst",
                "Financial Analyst"
            )
        )

    st.session_state["company"] = st.selectbox(
        "Choose a Company",
        (
            "Amazon",
            "Meta",
            "IBM",
            "Google",
            "LinkedIn",
            "Spotify"
        )
    )


    if st.button("Start Interview", on_click=complete_setup):
        st.write("Setup complete. Starting Interview...")


if (
    st.session_state.setup_complete
    and not st.session_state.feedback_shown
    and not st.session_state.chat_complete
):

    # Initializing the OpenAI client
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    # Setting up the OpenAI model
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o"

    # Initializing the system prompt and first question
    if not st.session_state.messages:
        st.session_state.messages = [
            {
                "role": "system",
                "content": (
                    "content": (
                        f"You are an HR executive interviewing a candidate "
                        f"called {st.session_state['name']} with experience "
                        f"{st.session_state['experience']} and skills "
                        f"{st.session_state['skills']}. "
                        f"You are interviewing the candidate for the position "
                        f"{st.session_state['level']} "
                        f"{st.session_state['position']} at "
                        f"{st.session_state['company']}. "
                        f"The interview contains exactly {MAX_QUESTIONS} questions. "
                        f"Ask only one question at a time. "
                        f"Continue directly from the previous candidate answer. "
                        f"Do not restart or reintroduce the interview. "
                        f"Do not introduce yourself or provide an interviewer name. "
                        f"Never use placeholders such as '[Your Name]'. "
                        f"Respond only with the next interview question. "
                        f"Do not add question numbers, counters, or the phrase "
                        f"'One Final Question' because the application adds them."
                    )
            },
            {
                "role": "assistant",
                "content": "Start by introducing yourself.",
                "question_number": 1
            }
        ]

    # Displaying stored messages
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                question_number = message.get("question_number")

                if question_number is not None:
                    st.markdown(
                        f"**[{question_number}/{MAX_QUESTIONS}]**"
                    )

                st.markdown(message["content"])

    # Accepting a maximum of five user answers
    if st.session_state.user_message_count < MAX_QUESTIONS:

        if prompt := st.chat_input("Your answer.", max_chars=1000):

            current_question = (
                st.session_state.user_message_count + 1
            )

            # Appending the user's answer
            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": prompt,
                    "question_number": current_question
                }
            )

            # Displaying the user's answer
            with st.chat_message("user"):
                st.markdown(
                    f"**[{current_question}/{MAX_QUESTIONS}]**"
                )
                st.markdown(prompt)

            st.session_state.user_message_count += 1

            # Generating the next question
            if (
                st.session_state.user_message_count
                < MAX_QUESTIONS
            ):

                next_question = (
                    st.session_state.user_message_count + 1
                )

                api_messages = [
                    {
                        "role": message["role"],
                        "content": message["content"]
                    }
                    for message in st.session_state.messages
                ]

                with st.chat_message("assistant"):
                    st.markdown(
                        f"**[{next_question}/{MAX_QUESTIONS}]**"
                    )

                    if next_question == MAX_QUESTIONS:
                        st.markdown("**One Final Question**")

                    stream = client.chat.completions.create(
                        model=st.session_state["openai_model"],
                        messages=api_messages,
                        stream=True
                    )

                    response = st.write_stream(stream)

                # Add the final-question label only to question five
                if next_question == MAX_QUESTIONS:
                    response = (
                        f"**One Final Question**\n\n{response}"
                    )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": response,
                        "question_number": next_question
                    }
                )

            else:
                st.session_state.chat_complete = True
                st.rerun()


if (
    st.session_state.chat_complete
    and not st.session_state.feedback_shown
):
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Fetching Feedback...")


if st.session_state.feedback_shown:
    st.subheader("Feedback")

    conversation_history = "\n".join(
        [
            f"{msg['role']}: {msg['content']}"
            for msg in st.session_state.messages
        ]
    )

    # Initialize a new OpenAI client for feedback
    feedback_client = OpenAI(
        api_key=st.secrets["OPENAI_API_KEY"]
    )

    # Generate feedback
    feedback_completion = (
        feedback_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful tool that provides "
                        "feedback on an interviewee's performance. "
                        "Before the feedback, give a score from 1 to 10. "
                        "Follow this format:\n"
                        "Overall Score: // Your score\n"
                        "Feedback: // Your feedback\n"
                        "Give only the feedback and do not ask "
                        "any additional questions."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        "This is the interview you need to evaluate. "
                        "Keep in mind that you are only a tool and "
                        "should not engage in conversation:\n"
                        f"{conversation_history}"
                    )
                }
            ]
        )
    )

    st.write(
        feedback_completion.choices[0].message.content
    )

    # Button to restart the interview
    if st.button("Restart Interview", type="primary"):
        streamlit_js_eval(
            js_expressions="parent.window.location.reload()"
        )
