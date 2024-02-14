import guidance
from guidance import gen, select
from textwrap import dedent


@guidance(stateless=False)
def cot(lm, question, max_depth=5):
    prompt = dedent(
        f"""\
        Please answer the following question, thinking it through step-by-step.
        Please respond by a series of "Thoughts" followed by your "Final Answer"

        Question: {question}
    """
    )
    done = False
    for i in range(1, max_depth):
        if i >= 1:
            lm += f"Thought {i}: "
        else:
            lm += select([f"Thought {i}: ", "Final Answer: "], name="action")
            if lm["action"] == "Final Answer: ":
                done = True
                break
        lm += gen(stop="\n", name="thoughts", list_append=True) + "\n"
    if not done:
        lm += "\nFinal Answer: "
    lm += gen(stop="\n", name="final_answer") + "\n"
    return lm
