from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# Local .env (en Render se ignora si no existe)
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY", "")

VS_ID = os.getenv("OPENAI_VECTOR_STORE_ID", "vs_6952d2458f088191b68d87b56ee02cad")
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.1")

APP_TITLE = "🍷🚢 KA Exportación de Vinos (Argentina)"
BANNER_FILE = "wine_banner.png"

st.set_page_config(page_title=APP_TITLE, page_icon="🍷", layout="wide")

# --- Header (imagen + título) ---
banner_path = Path(__file__).with_name(BANNER_FILE)
if banner_path.exists():
    st.image(str(banner_path), use_container_width=True)

st.title(APP_TITLE)
st.caption("Asistente KA para gestión de exportación de vinos desde Argentina (con búsqueda en tu Vector Store).")

# --- Validaciones ---
if not API_KEY:
    st.error("Falta OPENAI_API_KEY (ponelo en .env o en Environment Variables).")
    st.stop()

if not VS_ID:
    st.error("Falta OPENAI_VECTOR_STORE_ID (el id del vector store, ej: vs_...).")
    st.stop()

client = OpenAI(api_key=API_KEY)

# --- Estado conversacional ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "Sos un asistente KA especializado en exportación de vinos desde Argentina. "
                "Tu objetivo es ayudar a gestionar y explicar: documentación de comercio exterior "
                "(factura comercial, packing list, certificado de origen, BL/AWB, seguros), "
                "incoterms, logística (FCL/LCL, forwarders), aduana, etiquetado, requisitos por país, "
                "costos típicos, y mejores prácticas operativas. "
                "Respondé SIEMPRE en español, claro y accionable. "
                "Usá citas cuando existan en los documentos del Vector Store. "
                "Si no hay soporte documental suficiente en el Vector Store para una afirmación, decilo claramente "
                "y proponé qué documento faltaría o qué dato pedir. "
                "Respondé SOLO en base a los documentos disponibles en el Vector Store."
            ),
        }
    ]

# --- Render de historial ---
for m in st.session_state.messages:
    if m["role"] in ("user", "assistant"):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

user_text = st.chat_input("Escribí tu consulta sobre exportación de vinos… (ej: Incoterm recomendado, docs, costos, pasos)")

if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        placeholder = st.empty()

        # Responses API + tool file_search apuntando al Vector Store
        resp = client.responses.create(
            model=MODEL,
            input=st.session_state.messages,
            tools=[
                {
                    "type": "file_search",
                    "vector_store_ids": [VS_ID],
                }
            ],
        )

        answer_text = resp.output_text or "(sin respuesta)"
        placeholder.markdown(answer_text)

    st.session_state.messages.append({"role": "assistant", "content": answer_text})
