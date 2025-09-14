#### 🏗️ Activity #1:

Please evaluate your system on the following questions:

1. Explain the concept of object-oriented programming in simple terms to a complete beginner.
    - Aspect Tested: _Explain complex topics simple (elucidation)_
        - The text is legible, it properly parses indentation, and breaklines, however it does not do a good job parsing bold font style. It's overall acceptable and easy to read through.
        - Does not provide an explanation meant for a **complete beginner** it actually introduces advanced technical concepts which might be overwhelming initially like encapsulation, inheritance & polymorphism. It does not provide clear easy analogies which are helpful when simplifying complext topics

2. Read the following paragraph and provide a concise summary of the key points…
    - Aspect Tested: _Text comprenhension & Summarization_
        - It provided a legible format (not a summary though) which makes it more understandable than the original text.
        - The command was to provide a concise summary, however the response seemed like a rewrite of the text and breakdown into bullets, it is not a summary. In fact the response seems to be similar in length as the original text.

3. Write a short, imaginative story (100–150 words) about a robot finding friendship in an unexpected place.
    - Aspect Tested: _Creativity_
        - It returned a 141 words paragraph which alignes with the command given, it does a good job describing the scenario which accomplishes to catch the readers attention. It named the main character but not its friend (the mechanical bird) lacking in identity. Follows a chronological sentence. And closes the story gracefully with a nice message.

4. If a store sells apples in packs of 4 and oranges in packs of 3, how many packs of each do I need to buy to get exactly 12 apples and 9 oranges?
    - Aspect Tested: _Math Logic and Problem Solving skills_
        - Broke down the steps to resolve the calculation, making easier to understand the chain of thoughts.
        - Answer is accurate, also retried the commands few more times and it remained consistent. also changed the calculation and using the same logic it provided an accurate answer.

5. Rewrite the following paragraph in a professional, formal tone…
    - Aspect Tested: _Rewriting or tone shifting_
        - Text legibility is not improved.
        - Did not successfully accomplish the task, instead of shiting the tone, it returned a summary, it lacks in scientific terms which will make this more professional.
        - Added example from another LLM which does make a better job at shiting the tone.

**NOTE**:
- Used GPT4.1 mini
- Initial deployment still available at [Mushroom Kingdom AI *v1.0.0*](https://the-ai-engineer-challenge-coral.vercel.app)
    - Please see [answers_before_adjustments.md](answers_before_adjustments.md).
- New Enhanced deployment available at [Mushroom Kingdom AI *v1.1.0*](https://the-ai-engineer-challenge-ismgonza-ismgonzas-projects.vercel.app)
    - Please see [answers_after_adjustments.md](answers_after_adjustments.md).

#### ❓Question #1:

What are some limitations of vibe checking as an evaluation tool?
##### ✅ Answer:
    - It lacks in standard and structure making it very subjective to the "Vibe Checker" or Evaluator.
    - Relies in the points of interest (bias) of the Evaluator which could lean the final report to very specific points that might not be of interest for others, even a list of aspects were previously provided to the evaluator.
    - Relies in the background and knowledge of the evaluator.
    - It catches very obvious points but lacks in details like factual inconsistencies and hallucinations.
    - In summary, it could be a great tool as an initial "quick" check but it is very inconsistent.

### 🚧 Advanced Build (OPTIONAL):

#### 🏗️ Activity #1
##### Adjustments Made:
- Better AI Instructions
    - Updated the default system message with detailed guidelines for how the AI should respond to different types of questions
- Markdown Support
    - AI responses now display with proper markdown formatting (bold text, code blocks, lists, headers, colores, etc.)
- Shift+Enter for Line Breaks
    - You can now press Shift+Enter to add new lines in your message instead of sending it
- Multi-line Input
    - Changed the input box to a text area that grows as you type longer messages
- Updated Help Text
    - Added instructions showing users how to use the new Shift+Enter feature

##### Results:
1. The app is now providing simplified answers easier to understand, using analogies, not using advanced or complex concepts that can confuse the reader.
2. In terms of summarization, it is doing a much better job, reducing the text size while keeping important ideas.
3. Problem solving logic is improved, more explanatory and clearer to understand, while keeping the clear legible format.
4. Tone shifting is considerably improved as well, Text looks more professional without adding additional facts not included in the original text.
5. Additional enhancements are noticed like the hability to add new lines when inputing text 
