"""
Preview de qualidade do Google Cloud TTS Studio voices em PT-BR.

Gera o mesmo diálogo Ana/Lucas (OAuth vs OIDC) com vozes pt-BR-Studio.
Compare com /tmp/edge_tts_preview/preview.mp3 pra ouvir a diferença.

Setup:
    export GCP_TTS_API_KEY=<sua-api-key>
    python audio-worker/scripts/test_gcp_studio_tts.py

Saida: /tmp/gcp_studio_preview/preview.mp3
"""

import base64
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib import error, request
import json

VOICE_ANA = "pt-BR-Chirp3-HD-Kore"  # feminina (Chirp 3 HD)
VOICE_LUCAS = "pt-BR-Chirp3-HD-Charon"  # masculina (Chirp 3 HD)
API_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"

DIALOGUE: list[tuple[str, str]] = [
    ("Ana", "Bom dia! Hoje vou conversar com o Lucas sobre uma pegadinha que a FCC adora cobrar: a diferença entre OAuth 2.0 e OpenID Connect."),
    ("Lucas", "Ah, essa é clássica. Muita gente acha que são a mesma coisa, mas confundir os dois numa prova é perder a questão."),
    ("Ana", "Exato. Vamos começar pelo OAuth 2.0. Ele é um protocolo de autorização. Repare bem: autorização, não autenticação."),
    ("Lucas", "Isso. O OAuth 2.0 responde à pergunta: este aplicativo pode acessar quais recursos em nome do usuário? Ele entrega um access token, e esse token diz o que o app pode fazer."),
    ("Ana", "Já o OpenID Connect, o OIDC, é uma camada de autenticação construída em cima do OAuth 2.0."),
    ("Lucas", "Perfeito. O OIDC responde à pergunta: quem é este usuário? E ele faz isso adicionando um ID token, no formato JWT, que carrega as claims de identidade."),
    ("Ana", "Então a regra prática é: se a banca falar em access token, escopo, ou acesso a recurso, é OAuth. Se falar em ID token, claims, ou autenticação federada, é OIDC."),
    ("Lucas", "E cuidado com o enunciado FCC que troca os termos. Se aparecer OAuth autenticando usuário, está errado. OAuth autoriza acesso. OIDC autentica identidade."),
    ("Ana", "Resumo: OAuth é autorização, OIDC é autenticação sobre OAuth. Decora isso e você não erra mais."),
]


def synthesize(text: str, voice: str, api_key: str, retries: int = 3) -> bytes:
    body = json.dumps({
        "input": {"text": text},
        "voice": {"languageCode": "pt-BR", "name": voice},
        "audioConfig": {"audioEncoding": "MP3"},
    }).encode("utf-8")

    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        req = request.Request(
            f"{API_URL}?key={api_key}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
                return base64.b64decode(payload["audioContent"])
        except error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="replace")
            last_err = RuntimeError(f"HTTP {err.code}: {err_body}")
            if err.code in (429, 500, 502, 503, 504):
                wait = 2 * attempt
                print(f"    tentativa {attempt} falhou ({err.code}); retry em {wait}s...")
                time.sleep(wait)
                continue
            raise last_err
        except Exception as err:
            last_err = err
            time.sleep(2 * attempt)
    raise RuntimeError(f"falha apos {retries} tentativas: {last_err}")


def main() -> None:
    api_key = os.environ.get("GCP_TTS_API_KEY")
    if not api_key:
        print("ERRO: defina GCP_TTS_API_KEY no ambiente", file=sys.stderr)
        sys.exit(1)

    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg nao encontrado no PATH. Instale: sudo apt install ffmpeg")

    out_dir = Path("/tmp/gcp_studio_preview")
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Gerando {len(DIALOGUE)} turnos com Studio voices em {out_dir}...")

    parts: list[Path] = []
    for idx, (speaker, text) in enumerate(DIALOGUE):
        voice = VOICE_ANA if speaker == "Ana" else VOICE_LUCAS
        part_path = out_dir / f"{idx:03d}_{speaker}.mp3"
        audio = synthesize(text, voice, api_key)
        part_path.write_bytes(audio)
        parts.append(part_path)
        print(f"  [{idx + 1}/{len(DIALOGUE)}] {speaker} ({voice}) -> {part_path.name} ({len(audio) // 1024} KB)")

    concat_list = out_dir / "concat.txt"
    concat_list.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))

    final_path = out_dir / "preview.mp3"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            str(final_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    size_kb = final_path.stat().st_size / 1024
    total_chars = sum(len(t) for _, t in DIALOGUE)
    print(f"\nPronto: {final_path} ({size_kb:.1f} KB)")
    print(f"Caracteres consumidos: {total_chars} (free tier Studio = 1.000.000/mes)")


if __name__ == "__main__":
    main()
