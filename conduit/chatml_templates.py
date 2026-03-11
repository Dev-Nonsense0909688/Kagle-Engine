from jinja2 import Template

CHATML_CHAT_TEMPLATE = """{% for message in messages %}{{ '<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>\n' }}{% endfor %}{% if add_generation_prompt %}{{ '<|im_start|>assistant\n' }}{% endif %}"""

template = Template(CHATML_CHAT_TEMPLATE)


def chat_prompt(user, system):
    prompt = template.render(
        messages=[
            {
                "role": "system",
                "content": system,
            },
            {
                "role": "user",
                "content": user,
            },
        ],
        add_generation_prompt=True,
    )

    return prompt
