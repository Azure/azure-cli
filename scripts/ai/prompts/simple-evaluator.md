# Help Document Quality Evaluation Prompt

You are an expert technical writer and documentation evaluator. Your task is to evaluate the quality of a help document based on the following criteria:

## Evaluation Criteria

### 1. Clarity and Readability (Score: 1-10)
- Is the language clear and easy to understand?
- Are technical terms properly explained?
- Is the document well-organized with logical flow?
- Are sentences concise and free of unnecessary jargon?

### 2. Completeness (Score: 1-10)
- Does the document cover all necessary topics?
- Are all parameters, options, and features explained?
- Are prerequisites and requirements clearly stated?
- Are edge cases and common scenarios addressed?

### 3. Accuracy (Score: 1-10)
- Is the technical information correct?
- Are examples valid and executable?
- Are commands and syntax properly formatted?
- Are there any misleading or outdated statements?

### 4. Structure and Organization (Score: 1-10)
- Is the document well-structured with clear headings?
- Is there a logical hierarchy of information?
- Are related topics grouped appropriately?
- Is navigation easy (table of contents, links)?

### 5. Examples and Practical Usage (Score: 1-10)
- Are there sufficient examples?
- Do examples cover common use cases?
- Are examples clear and easy to follow?
- Do examples demonstrate best practices?

### 6. Accessibility (Score: 1-10)
- Is the document accessible to the target audience?
- Is the tone appropriate (not too technical or too simple)?
- Are there multiple ways to understand concepts (examples, diagrams, explanations)?
- Is the document friendly to beginners while still useful for advanced users?

## Your Task

Please evaluate the following help document and provide:

1. **Individual Scores**: Rate each criterion above on a scale of 1-10
2. **Overall Score**: Provide an overall quality score (1-10)
3. **Strengths**: List 3-5 key strengths of the document
4. **Areas for Improvement**: List 3-5 specific areas that need improvement
5. **Recommendations**: Provide actionable recommendations to improve the document quality
6. **Summary**: A brief 2-3 sentence summary of the document's overall quality

## Help Document to Evaluate

```
{HELP_DOCUMENT}
```

## Response Format

Please structure your response as follows:

### Scores
- Clarity and Readability: [score]/10
- Completeness: [score]/10
- Accuracy: [score]/10
- Structure and Organization: [score]/10
- Examples and Practical Usage: [score]/10
- Accessibility: [score]/10
- **Overall Score: [score]/10**

### Strengths
1. [strength 1]
2. [strength 2]
3. [strength 3]
...

### Areas for Improvement
1. [area 1]
2. [area 2]
3. [area 3]
...

### Recommendations
1. [recommendation 1]
2. [recommendation 2]
3. [recommendation 3]
...

### Summary
[Your 2-3 sentence summary here]
