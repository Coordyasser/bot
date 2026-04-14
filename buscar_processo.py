"""
Busca processo judicial no Escavador usando Playwright.
Uso: python buscar_processo.py "0840531-51.2024.8.18.0140" "chat_id"
"""
import sys
import json
import asyncio
import re
from playwright.async_api import async_playwright

async def buscar(numero_processo, chat_id):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto("https://www.escavador.com/processos", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            # Aceita cookies se aparecer
            try:
                await page.click("text=Continuar", timeout=3000)
                await page.wait_for_timeout(1500)
            except:
                pass

            # Preenche o campo de busca pelo id correto
            await page.fill("#search-box-input", numero_processo)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(5000)

            texto = await page.evaluate("() => document.body.innerText")

            await browser.close()

            # Extrai apenas a parte relevante do texto
            linhas = [l.strip() for l in texto.split('\n') if l.strip()]

            # Procura pelo bloco do processo
            inicio = -1
            for i, linha in enumerate(linhas):
                if numero_processo in linha or numero_processo.replace("-","").replace(".","") in linha.replace("-","").replace(".",""):
                    inicio = max(0, i - 1)
                    break

            if inicio >= 0:
                bloco = '\n'.join(linhas[inicio:inicio+30])
            else:
                # Pega qualquer resultado relevante
                bloco = '\n'.join(linhas[:40])

            resposta = f"Processo {numero_processo}\n\n{bloco}"

            return {
                "chat_id": chat_id,
                "process_number": numero_processo,
                "response": resposta[:3000]
            }

        except Exception as e:
            await browser.close()
            return {
                "chat_id": chat_id,
                "process_number": numero_processo,
                "response": f"Erro ao consultar: {str(e)}"
            }

if __name__ == "__main__":
    numero = sys.argv[1] if len(sys.argv) > 1 else "0840531-51.2024.8.18.0140"
    chat_id = sys.argv[2] if len(sys.argv) > 2 else "test"
    result = asyncio.run(buscar(numero, chat_id))
    sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"))
    sys.stdout.buffer.write(b"\n")
