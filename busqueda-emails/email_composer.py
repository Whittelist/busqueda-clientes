import os
from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, LLM_TEMPERATURE


def llm_client() -> OpenAI:
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("Define DEEPSEEK_API_KEY en .env")
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


PROMPTS = {
    1: """
Eres Silvia Perea, co-fundadora de Silvigon.

Redacta un email para {nombre} ({categoria} en {provincia}).

PROBLEMAS REALES DEL SECTOR (usa esto como base):
- Todo se registra todavia en papel (partes, albaranes, ensayos, documentacion)
- Gente haciendo tareas manuales en el ordenador que no aportan valor
- Documentos desorganizados, dificiles de encontrar cuando se necesitan
- No tienen un ERP ni un lugar central donde ver el estado de la empresa
- Quieren digitalizarse pero no saben por donde empezar ni si es caro
- No saben lo que la IA puede hacer por su negocio

INSTRUCCIONES:
- Maximo 100 palabras.
- Empezar con UNA observacion HUMANA y REAL sobre su sector.
- Sonar a alguien que conoce el sector de verdad, no a un comercial.
- NO usar: "solucion integral", "optimizacion", "sinergias", "digitalizacion", "transformacion digital".
- NO asumir que tienen WooCommerce ni tienda online si no se menciona.
- Ofrecer consulta GRATUITA de 15 min SIN COMPROMISO.
- Pregunta final sencilla (ej: "¿Te parece si hablamos 15 minutos?").

REGLAS SOBRE RESENAS DE CLIENTES (IMPORTANTE):
- Si hay resenas disponibles, USALAS para entender los problemas del sector o de la empresa, pero:
  - NUNCA menciones que has visto sus resenas
  - NUNCA copies textualmente una resena
  - NUNCA digas "tus clientes dicen que..." o "he visto en vuestras resenas que..."
  - Enmarcalo siempre como conocimiento general del sector:
    - BIEN: "En el sector del prefabricado, los plazos de entrega suelen ser un quebradero de cabeza"
    - MAL: "He visto que vuestros clientes se quejan de los plazos de entrega"
  - Si las resenas son positivas, NO las menciones en absoluto
  - Usa las resenas solo para IDENTIFICAR que problemas podrian tener, no como fuente citable
- Devuelve SOLO el cuerpo del email, sin asunto, sin firma.
""",

    2: """
Eres Silvia Perea, co-fundadora de Silvigon. Ya enviaste un primer email a {nombre} ({categoria} en {provincia}) pero no respondieron.

Este es el SEGUNDO email.

INSTRUCCIONES:
- Maximo 90 palabras.
- NO empezar con "te escribi la semana pasada".
- Segundo angulo: centrarse en que siguen perdiendo tiempo con tareas que una maquina podria hacer (gestion de documentos, registros repetitivos, partes de trabajo).
- Tono natural y cercano.
- Sin compromiso, sin presion.
- NO mencionar reviews, reputacion online, ni opiniones de clientes directamente.
- Devuelve SOLO el cuerpo del email, sin asunto, sin firma.
""",

    3: """
Eres Silvia Perea, co-fundadora de Silvigon. Has enviado 2 emails a {nombre} ({categoria} en {provincia}) sin respuesta.

Este es el TERCER email. ES EL UNICO donde NO se pide NADA.

INSTRUCCIONES:
- Maximo 80 palabras.
- NO pedir reunion, ni llamada, ni respuesta.
- Compartir UNA reflexion util sobre el sector.
- Tono: util, desinteresado, profesional.
- Cerrar con un "Sin mas, un saludo".
- NO mencionar reviews, reputacion online, ni opiniones de clientes directamente.
- Devuelve SOLO el cuerpo del email, sin asunto, sin firma.
""",

    4: """
Eres Silvia Perea, co-fundadora de Silvigon. Has enviado 3 emails a {nombre} ({categoria} en {provincia}) sin respuesta.

Este es el CUARTO email. Pregunta concreta y facil de responder.

INSTRUCCIONES:
- Maximo 90 palabras.
- Empezar con naturalidad.
- Hacer UNA pregunta sobre como gestionan algo basico hoy en dia.
- Ofrecer: "Si quieres, en 15 minutos te enseno como otros lo estan resolviendo."
- Sin compromiso, sin presion.
- NO mencionar reviews, reputacion online, ni opiniones de clientes directamente.
- Devuelve SOLO el cuerpo del email, sin asunto, sin firma.
""",

    5: """
Eres Silvia Perea, co-fundadora de Silvigon. Has enviado 4 emails a {nombre} ({categoria} en {provincia}) sin respuesta.

QUINTO Y ULTIMO email.

INSTRUCCIONES:
- Maximo 70 palabras.
- MUY humano.
- "Entiendo que estais liados o no es el momento"
- No insistir. No presionar.
- "Si en algun momento surge algo relacionado con automatizacion o simplemente quereis saber como funciona esto, aqui estamos"
- Despedida tranquila.
- NO mencionar reviews, reputacion online, ni opiniones de clientes.
- Devuelve SOLO el cuerpo del email, sin asunto, sin firma.
""",
}

FIRMA = "\n--\nSilvia Perea\nCo-fundadora, Silvigon"


def generar_email(nombre: str, categoria: str, provincia: str, problema: str, idea: str, tamano: str, web: str, touch: int, contexto_extra: str = "") -> str:
    """
    Genera un email personalizado usando DeepSeek.
    contexto_extra: informacion adicional de la fila del Sheet (telefono, direccion, reviews, notas, etc.)
    """
    prompt = PROMPTS.get(touch)
    if not prompt:
        raise ValueError(f"Touch {touch} no valido (1-5)")

    prompt_filled = prompt.format(
        nombre=nombre,
        categoria=categoria,
        provincia=provincia,
        problema=problema or "No especificado",
        idea=idea or "No especificado",
        tamano=tamano or "No especificado",
        web=web or "No disponible"
    )

    system = (
        "Eres un redactor de emails B2B para Silvigon. "
        "Escribes en espanol de Espana, con tono humano, natural y concreto. "
        "No inventes datos: usa solo el contexto proporcionado. "
        "Devuelve SOLO el texto del email, sin formato markdown, sin JSON."
    )

    if contexto_extra:
        system += f"\n\nINFORMACION ADICIONAL SOBRE LA EMPRESA (usala si es relevante):\n{contexto_extra}"

    client = llm_client()
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt_filled},
        ],
        temperature=LLM_TEMPERATURE,
        max_tokens=300,
    )

    cuerpo = (response.choices[0].message.content or "").strip()
    for token in ["```text", "```", "```json", "```plaintext"]:
        cuerpo = cuerpo.replace(token, "")
    cuerpo = cuerpo.strip()

    # Fallback si IA devuelve vacio
    if not cuerpo or len(cuerpo) < 20:
        cuerpo = _fallback_email(nombre, categoria, provincia, problema, idea, tamano, touch)

    return cuerpo + FIRMA


_FALLBACKS = {
    1: "Hola,\n\nVeo que trabajáis con {categoria} en {provincia}. Desde Silvigon ayudamos a empresas del sector construcción a simplificar procesos con tecnología. ¿Te parece si hablamos 15 minutos sin compromiso?",
    2: "Hola,\n\nSolo un rápido seguimiento. En el sector {categoria}, la automatización de procesos repetitivos puede liberar mucha carga al equipo. Si te interesa ver cómo aplica a tu caso, respondeme a este correo.",
    3: "Hola,\n\nSolo quería compartir una observación: muchas empresas de {categoria} siguen gestionando procesos manualmente cuando ya hay formas más sencillas de hacerlo. Sin más, un saludo.",
    4: "Hola,\n\nUna pregunta rápida: ¿cómo gestionáis actualmente la coordinación entre los pedidos y la producción en {categoria}? Si quieres, en 15 minutos te enseño cómo otros lo están simplificando.",
    5: "Hola,\n\nEntiendo que probablemente estéis liados o no sea el momento. Sin problema. Si en algún momento surge algo relacionado con automatización o IA, aquí estamos. Un saludo.",
}


def _fallback_email(nombre: str, categoria: str, provincia: str, problema: str, idea: str, tamano: str, touch: int) -> str:
    template = _FALLBACKS.get(touch, "")
    if not template:
        return "Hola,\n\nQuedo a tu disposición para lo que necesites."
    return template.format(nombre=nombre, provincia=provincia, categoria=categoria)
