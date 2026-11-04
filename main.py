import os
from utils.text_parser_to_json import open_json_file
from dotenv import load_dotenv
from google import genai
from models.classification import ClassificationResponse
from models.summary import SummarizationResponse

MODEL_ID = "gemini-3.6-flash"

load_dotenv()

if not os.getenv("GEMINI_API_KEY"):
    raise RuntimeError("GEMINI_API_KEY is missing. Check your .env file.")

client = genai.Client()


def assign_article_ids(articles: list[dict]) -> list[dict]:

    for index, article in enumerate(articles, start=1):
        article["id"] = f"a{index:03d}"

    return articles


def create_article_lookup(articles: list[dict]) -> dict:

    return {
        article["id"]: {"title": article["title"], "content": article["content"]}
        for article in articles
    }


def main():
    json_articles = open_json_file("data/test_samples.json")
    compiled_articles = str()
    keys = ["id", "title", "content"]

    articles = assign_article_ids(json_articles)
    articles_lookup = create_article_lookup(articles)

    for article in articles[:50]:
        for key in keys:
            compiled_articles += f"{key}: {article[key]}\n"

        compiled_articles += "\n\n"

    classifier_prompt = f"""
    You are a Philippine national news classification system.

    Your task is to identify whether a news article is MAJOR or NON-MAJOR
    based on its actual or potential impact on Filipinos.

    CLASSIFICATION RULES:
    1. Geographic Impact
    - The news SHOULD have an impact inside the Philippines.
    - It SHOULD affect at least one of the three major island groups:
    Luzon, Visayas, or Mindanao.
    - The impact SHOULD be geographically widespread.
    - News limited to a single barangay, city, province, or region
    SHOULD generally be classified as NON-MAJOR.
    - However, news affecting a substantial population within one
    major island group can still qualify as MAJOR.

    2. Population Impact
    - The news SHOULD affect or potentially affect many Filipinos.
    - Consider the number of people affected, directly or indirectly.
    - Consider whether the issue could affect other communities
    beyond its immediate location.

    3. Significance
    - The news SHOULD be significant or nationally relevant.
    - It COULD have short-term or long-term consequences.
    - It COULD have positive or negative effects.
    - Seasonal and weekly developments are acceptable, including
    weather conditions and economic fluctuations.

    4. Impact Assessment
    Evaluate the following:
    - Does the news affect Luzon, Visayas, or Mindanao?
    - Is its geographic reach national or localized?
    - Does it affect a substantial population?
    - Is its impact short-term or long-term?
    - Is it nationally significant?
    - Does it have positive or negative consequences?
    - Could its effects extend beyond its immediate location?

    DECISION RULES:

    Classify as MAJOR when:
    - It has substantial geographic or population impact.
    - It affects or potentially affects many Filipinos.
    - It has meaningful national or major-island significance.

    Classify as NON-MAJOR when:
    - Its effects are primarily isolated to a small locality.
    - It has limited population impact.
    - It lacks broader significance or potential consequences.

    Do not classify news as MAJOR simply because it involves
    government officials, public figures, or nationally known institutions.
    Evaluate the actual or potential impact of the event.

    OUTPUT RULES:

    1. Return every article exactly once.
    2. Use the original article ID provided in the input.
    3. Do not generate new IDs.
    4. Do not reproduce article titles or contents.
    5. Assign exactly one category: MAJOR or NON-MAJOR.
    6. Do not omit articles.
    7. Return valid JSON following the required schema.

    ARTICLES TO CLASSIFY:
    {compiled_articles}
    """

    classifier_response = client.models.generate_content(
        model=MODEL_ID,
        contents=classifier_prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": ClassificationResponse,
        },
    )

    if classifier_response.text is None:
        raise ValueError("Gemini returned an empty response.")

    # 5. Parse structured response
    classification_results = ClassificationResponse.model_validate_json(
        classifier_response.text
    )

    # 6. Map IDs to original articles
    major_articles = []

    for result in classification_results.results:

        if result.category == "MAJOR":

            article = articles_lookup.get(result.id)

            if article is not None:
                major_articles.append(
                    {
                        "id": result.id,
                        "title": article["title"],
                        "content": article["content"],
                    }
                )

    # # 7. Display results
    # print("Total classified:", len(classification_results.results))
    # print("Major articles:", len(major_articles))

    # for article in major_articles:
    #     print(article["id"])
    #     print(article["title"])
    #     print(article["content"])
    #     print("-" * 50)

    compiled_major_articles = str()
    for article in major_articles:
        compiled_major_articles += f"Title: {article["title"]}\n"
        compiled_major_articles += f"Content: {article["content"]}\n\n"

    summarizer_prompt = f"""
    You are a Philippine news summarization system. Your task is to simplify news articles so that ordinary Filipino readers can easily understand them
    and an explanatory news analyst for InformedPH, and your responsibility is to help ordinary Filipino readers understand the real-world significance of reported news.

    Objective
    - Explain how the reported event, decision, development, or situation could affect people, communities, businesses, and the Philippines.
    - DO NOT merely define terms or explain the background of concepts. Prioritize the practical consequences and implications of the news.
    
    Summarization Rules:
    1. Simplify the News
    - Rewrite complex sentences using clear, simple, and accessible language.
    - Avoid unnecessary jargon, technical terms, and overly complicated explanations.
    - Keep the summary concise while retaining the most important information.
    - Prioritize the key events, people, locations, dates, and relevant details.

    2. Preserve the Original Context
    - DO NOT change the original meaning, context, or intent of the article.
    - DO NOT introduce assumptions, personal opinions, or unsupported information.
    - DO NOT exaggerate or downplay the significance of the event.
    - Preserve important facts, figures, statistics, and statements.
    - DO NOT remove details that are necessary to understand the event.

    3. Preserve the Original Title
    - DO NOT rewrite, modify, shorten, or replace the original article title.
    - Retain the exact title provided in the input.

    4. Accuracy and Reliability
    - Use only information supported by the original article.
    - DO NOT fabricate information or fill gaps with assumptions.
    - If information is unclear or insufficient, do not attempt to invent an explanation.

    5. Strictly Follow the Provided Articles
    - Treat the provided article content as the sole source of information.
    - ONLY use facts, details, and information explicitly supported by the provided article.
    - DO NOT introduce external information, background knowledge, assumptions, or personal interpretations.
    - DO NOT combine information from different articles unless explicitly instructed.
    - DO NOT invent details to fill gaps in the original article.
    - DO NOT present speculation, predictions, or unverified claims as established facts.
    - When information is missing or unclear, do not attempt to fill in the missing details.

    6. Summary Length and Information Retention
    - Produce informative summaries, not merely brief descriptions or rewritten headlines.
    - Retain the essential details necessary for readers to understand the news without having to read the original article.
    - Include relevant information from the source article, such as:
        - What happened?
        - Who or what was involved?
        - Where and when did it happen?
        - Why did it happen, if explained in the article?
        - What are its consequences or potential implications, if discussed in the article?
        - Important figures, statistics, dates, statements, and developments.
    - DO NOT excessively shorten the article by removing relevant information.
    - DO NOT FORCE every summary into a single sentence. Use multiple sentences when necessary to communicate the important details.
    - AVOID unnecessary repetition, background information, and details that do not contribute to understanding the main event.
    - The summary should be shorter than the original article while retaining its essential information and context.
    - Use approximately 3–5 sentences as a general guideline. The appropriate length may vary depending on the complexity and amount of relevant information in the original article.
    - DO NOT add information simply to reach the suggested sentence count. Factual accuracy and completeness take priority over length.
    
    7. Explanation rules:
    - EXPLAIN the relationships between the facts presented in the article.
    - Use practical examples when they help readers understand the subject.
    - DO NOT simply repeat or rewrite the summary.
    - DO NOT introduce unsupported facts, assumptions, or external information.
    - Distinguish between confirmed facts, statements made by individuals or organizations, and potential consequences.
    - If the article DOES NOT provide enough information for a deeper explanation, explain only what can reasonably be understood from its contents.
    - Focus on real-world effects. Explain how the reported development could affect ordinary Filipinos and relevant groups, such as households, workers, students, farmers, businesses, or communities.
    - EXPLAIN practical consequences. When relevant, discuss possible effects on food prices, transportation, employment, livelihoods, household expenses, public safety, education, health, or access to essential services.
    - EXPLAIN why the news matters. Connect the reported development to its broader significance for affected people and the country.
    - Discuss both positive and negative effects when applicable. Do not force both perspectives when the news primarily presents one type of impact.
    - Use concrete examples. When useful, illustrate how the reported development could affect people's everyday lives.
    - EXPLAIN technical concepts only when necessary. Define unfamiliar terms briefly when doing so helps readers understand the event or its consequences. Do not make definitions the main purpose of the explanation.
    - Distinguish actual effects from potential effects. Use appropriate wording such as "could," "may," or "might" when consequences are possible but not confirmed.
    - DO NOT invent consequences. Every explanation must be supported by the original article or reliable, relevant background information explicitly provided to you.
    - DO NOT exaggerate. Avoid sensationalism, unsupported predictions, and claims that imply certainty about uncertain outcomes.
    - AVOID repeating the summary. Assume the reader has already read the summary. Focus on helping them understand its significance.
    - Remain neutral. DO NOT insert personal opinions or political judgments.
    - If meaningful implications cannot be established, explain the direct practical significance supported by the available information rather than manufacturing an impact.

    Output Requirements:
    - Return the exact original article title.
    - Return the simplified news summary.
    - Return one clear, informative explanation in simple language.
    - Prioritize helping readers answer:
        - Who could be affected?
        - How could they be affected?
        - Why does this development matter?
    - DO NOT reproduce the entire original article.
    - DO NOT include introductory remarks or additional commentary.
    - Follow the required structured output schema.

    PROVIDED ARTICLES:
    {compiled_major_articles}
    """

    summarizer_response = client.models.generate_content(
        model=MODEL_ID,
        contents=summarizer_prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": SummarizationResponse,
        },
    )

    if summarizer_response.text is None:
        raise ValueError("Gemini Summarizer returned an empty response.")

    summarization_results = SummarizationResponse.model_validate_json(
        summarizer_response.text
    )

    for result in summarization_results.results:
        print("Title: ", result.title)
        print("Summary: ", result.summary)
        print("Explanation: ", result.explantion)
        print("\n\n")


if __name__ == "__main__":
    main()
