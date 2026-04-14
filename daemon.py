"""
Servidor HTTP para receber requisicoes do n8n, buscar processo no Escavador
e devolver os dados para o webhook do n8n.
"""
import json
import os
import subprocess
import re
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
N8N_WEBHOOK = "https://n8nevo-n8n-webhook.3fmybz.easypanel.host/webhook/b7185ac4-1129-4719-bb8e-c567b18b36a2"
HTTP_PORT = 5055


def notify_n8n(client_chat_id, process_number, response):
    """Envia os dados do processo para o webhook do n8n."""
    try:
        match = re.search(r'\{[\s\S]*"response"[\s\S]*\}', response)
        if match:
            payload_dict = json.loads(match.group())
        else:
            payload_dict = {
                "chat_id": str(client_chat_id),
                "process_number": process_number,
                "response": response
            }
    except Exception:
        payload_dict = {
            "chat_id": str(client_chat_id),
            "process_number": process_number,
            "response": response
        }

    payload = json.dumps(payload_dict, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        N8N_WEBHOOK,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            print(f"[N8N] Webhook enviado: {payload_dict}", flush=True)
    except Exception as e:
        print(f"[N8N] Erro ao enviar webhook: {e}", flush=True)


def buscar_processo(process_number, client_chat_id):
    """Busca processo no Escavador via Playwright."""
    try:
        result = subprocess.run(
            ["python", os.path.join(WORK_DIR, "buscar_processo.py"), process_number, str(client_chat_id)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
            cwd=WORK_DIR,
            env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONLEGACYWINDOWSSTDIO": "0"}
        )
        output = result.stdout.strip()
        if output:
            return output
        stderr = result.stderr.strip()
        if stderr:
            print(f"[ERRO] buscar_processo stderr: {stderr[:300]}", flush=True)
    except subprocess.TimeoutExpired:
        print("[ERRO] buscar_processo: timeout 300s", flush=True)
    except Exception as e:
        print(f"[ERRO] buscar_processo: {e}", flush=True)
    return None


def processar_consulta(process_number, client_chat_id):
    """Processa consulta e notifica o n8n."""
    print(f"[PROCESSO] Consultando: {process_number} | chat_id: {client_chat_id}", flush=True)
    response = buscar_processo(process_number, client_chat_id)
    if not response:
        response = json.dumps({
            "chat_id": str(client_chat_id),
            "process_number": process_number,
            "response": "Nao foi possivel consultar o processo. Tente novamente ou entre em contato pelo WhatsApp (86 99435-6139)."
        }, ensure_ascii=False)
    print(f"[RESP] {response[:200]}", flush=True)
    notify_n8n(client_chat_id, process_number, response)


class N8NHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Silencia logs HTTP

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body)

            process_number = data.get("process_number", "").strip()
            client_chat_id = str(data.get("chat_id", ""))

            print(f"[HTTP] Recebido: process={process_number} chat_id={client_chat_id}", flush=True)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')

            t = threading.Thread(target=processar_consulta, args=(process_number, client_chat_id))
            t.daemon = True
            t.start()

        except Exception as e:
            print(f"[HTTP ERRO] {e}", flush=True)
            self.send_response(500)
            self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"online"}')


print("=" * 50, flush=True)
print("Servidor HTTP iniciado!", flush=True)
print(f"Porta: {HTTP_PORT}", flush=True)
print(f"ngrok: https://known-directly-halibut.ngrok-free.app", flush=True)
print("=" * 50, flush=True)

server = HTTPServer(("0.0.0.0", HTTP_PORT), N8NHandler)
server.serve_forever()
