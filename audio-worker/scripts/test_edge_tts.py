"""
Preview de qualidade do Edge TTS em PT-BR multi-voice.

Gera um diálogo curto Ana/Lucas sobre uma pegadinha FCC clássica
(OAuth 2.0 vs OIDC) e concatena num único mp3 com ffmpeg.

Uso:
    pip install edge-tts
    python audio-worker/scripts/test_edge_tts.py

Saída: /tmp/edge_tts_preview/preview.mp3
"""

import asyncio
import shutil
import subprocess
from pathlib import Path

import edge_tts

VOICE_ANA = "pt-BR-FranciscaNeural"
VOICE_LUCAS = "pt-BR-AntonioNeural"

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


async def synthesize_turn(text: str, voice: str, out_path: Path, retries: int = 4) -> None:
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(out_path))
            return
        except Exception as err:
            last_err = err
            wait = 2 * attempt
            print(f"    tentativa {attempt} falhou ({type(err).__name__}); retry em {wait}s...")
            await asyncio.sleep(wait)
    raise RuntimeError(f"falha ao sintetizar apos {retries} tentativas: {last_err}")


async def main() -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg nao encontrado no PATH. Instale: sudo apt install ffmpeg")

    out_dir = Path("/tmp/edge_tts_preview")
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Gerando {len(DIALOGUE)} turnos em {out_dir}...")

    parts: list[Path] = []
    for idx, (speaker, text) in enumerate(DIALOGUE):
        voice = VOICE_ANA if speaker == "Ana" else VOICE_LUCAS
        part_path = out_dir / f"{idx:03d}_{speaker}.mp3"
        await synthesize_turn(text, voice, part_path)
        parts.append(part_path)
        print(f"  [{idx + 1}/{len(DIALOGUE)}] {speaker} ({voice}) -> {part_path.name}")

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
    print(f"\nPronto: {final_path} ({size_kb:.1f} KB)")
    print("Reproduza com: mpv ou xdg-open, ou copie pro Windows e abra com qualquer player.")


if __name__ == "__main__":
    asyncio.run(main())
