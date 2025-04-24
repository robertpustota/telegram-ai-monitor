import dspy
from app.core.config import get_settings

config = get_settings()


class PostRelevanceChecker(dspy.Signature):
    """Checks if a post is relevant to a given topic."""
    
    post_content: str = dspy.InputField(desc="Post content to analyze")
    topic_name: str = dspy.InputField(desc="Topic name")
    topic_description: str = dspy.InputField(desc="Topic description", default=None)
    is_relevant: bool = dspy.OutputField(desc="Whether the post is relevant to the topic True or False")


class RelevancePredictor(dspy.Module):
    def __init__(self, llm_model: str = "gpt-4o-mini", llm_model_kwargs: dict = {}):
        super().__init__()
        self.llm_model = llm_model
        self.llm_model_kwargs = llm_model_kwargs
        self.checker = dspy.Predict(PostRelevanceChecker)
        
    def forward(self, post_content: str, topic_name: str, topic_description: str = None) -> bool:
        result = self.checker(
            post_content=post_content,
            topic_name=topic_name,
            topic_description=topic_description
        )
        return result.is_relevant

    def invoke(self, post_content: str, topic_name: str, topic_description: str = None) -> bool:
        with dspy.settings.context(lm=dspy.LM(self.llm_model, **self.llm_model_kwargs)):
            return self.forward(post_content, topic_name, topic_description)


def check_post_relevance(post_content: str, topic_name: str, topic_description: str = None) -> bool:
    predictor = RelevancePredictor(llm_model="gpt-4o-mini", llm_model_kwargs={"api_key": config.OPENAI_API_KEY})
    return predictor.invoke(post_content, topic_name, topic_description)
