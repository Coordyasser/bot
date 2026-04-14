"""
Busca processo judicial no Escavador usando Playwright com login.
Uso: python buscar_processo.py "1008837-57.2024.8.26.0011" "chat_id"
"""
import sys
import json
import asyncio
import re
from playwright.async_api import async_playwright

EMAIL = "lucasmelosiqueira1@gmail.com"
SENHA = "Isabela1999!"

async def buscar(numero_processo, chat_id):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            # Login no Escavador
            await page.goto("https://www.escavador.com/login", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)

            await page.fill("input[type=email], input[name=email]", EMAIL)
            await page.fill("input[type=password], input[name=password]", SENHA)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(3000)

            # Busca o processo
            await page.goto("https://www.escavador.com/processos", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)

            await page.fill("#search-box-input", numero_processo)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(5000)

            texto = await page.evaluate("() => document.body.innerText")
            await browser.close()

            linhas = [l.strip() for l in texto.split('\n') if l.strip()]

            inicio = -1
            for i, linha in enumerate(linhas):
                if numero_processo in linha or numero_processo.replace("-","").replace(".","") in linha.replace("-","").replace(".",""):
                    inicio = max(0, i - 1)
                    break

            if inicio >= 0:
                bloco = '\n'.join(linhas[inicio:inicio+40])
            else:
                bloco = '\n'.join(linhas[:50])

            resposta = f"Processo {numero_processo}\n\n{bloco}"

            return {
                "chat_id": chat_id,
                "process_number": numero_processo,
                "response": resposta[:4000]
            }

        except Exception as e:
            await browser.close()
            return {
                "chat_id": chat_id,
                "process_number": numero_processo,
                "response": f"Erro ao consultar: {str(e)}"
            }

if __name__ == "__main__":
    numero = sys.argv[1] if len(sys.argv) > 1 else "1008837-57.2024.8.26.0011"
    chat_id = sys.argv[2] if len(sys.argv) > 2 else "test"
    result = asyncio.run(buscar(numero, chat_id))
    sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"))
    sys.stdout.buffer.write(b"\n")
