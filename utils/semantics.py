from semantic_router import Route
from semantic_router.encoders import CohereEncoder
from semantic_router.routers import SemanticRouter
from config.env import env

chitchat = Route(
    name='chitchat',
    utterances=[
        "How's the weather today?",
        "Nice day, isn't it?",
        "How was your weekend?",
        "Got any plans for the weekend?",
        "What did you do last night?",
        "Did you watch the game?",
        "How’s your day going?",
        "Been keeping busy?",
        "Long time no see!",
        "How's work treating you?",
        "Did you see that news story?",
        "What’s new with you?",
        "How have you been?",
        "What’s your favorite food?",
        "This weather is crazy, huh?",
        "I can’t believe how hot it is.",
        "Cold enough for you?",
        "Did you hear about the traffic?",
        "How’s your morning going?",
        "Ready for the weekend?",
        "The week’s flying by!",
        "Mondays, am I right?",
        "Almost Friday!",
        "How’s life?",
        "Busy day?",
        "Quiet day at work?",
        "How do you usually spend your evenings?",
        "Any good TV shows lately?",
        "What kind of music do you like?",
        "Been to any concerts recently?",
        "Did you sleep well?",
        "Had your coffee yet?",
        "Do you have any pets?",
        "Are you a morning person?",
        "Do you work from home?",
        "What’s your favorite holiday?",
        "Have you traveled anywhere recently?",
        "Any recommendations for a movie?",
        "Do you like cooking?",
        "Did you catch the news this morning?",
        "What's your go-to lunch?",
        "Do you like working here?",
        "Are you into sports?",
        "Big plans this evening?",
        "Ever been to [local place]?",
        "Nice shoes!",
        "I like your outfit!",
        "You seem in a good mood today.",
        "It’s been a while since we talked.",
        "I feel like I haven’t seen you in forever.",
        "Got any hobbies?",
    ]
    # utterances = [
    #     "How are you?",
    #     "How’s your day?",
    #     "What's up?",
    #     "Hope you're well.",
    #     "Any weekend plans?",
    #     "Did you watch the game?",
    #     "Busy day?",
    #     "Do you work remotely?",
    #     "Got any hobbies?",
    #     "Seen any good shows lately?",
    # ]
)

nocontext = Route(
    name='nocontext',
    utterances = [
        "I'm sorry, but the company policies do not mention any reference for bereavement policy FAQs.",
        "I don't have specific information about burnout available at the moment. I'm unable to provide details on this particular question.",
        "I am unable to provide specific information about that right now.",
        "I don't have specific information",
        "I don't have specific information about the starting section of a prompt. I'm unable to provide details on this particular question as the company policies do not mention any reference for your query explicitly."
        "I'm unable to locate enough information to answer this accurately.",
        "I'm sorry, but the policies do not mention the promotions available based on the years of experience."
        "I don't have specific information about that topic available at the moment.",
        "This question may be outside the scope of what’s currently documented.",
    ]
)

referral_policy = Route(
    name='referral_policy',
    utterances=[
        "Are employees eligible for referral bonuses?",
        "Can I refer someone who used to work here?",
        "Do referrals apply to ex-employees?",
        "What are the rules around referring former employees?",
        "Is there a reward for referring ex-colleagues?",
        "Can I get referral benefits if the person worked here before?",
        "Are ex-employees eligible to be referred?",
        "Is there a referral policy for rehires?",
        "Are there exceptions to the referral policy for former employees?",
    ]
)



routes = [chitchat, nocontext]
encoder = CohereEncoder(
    name="embed-english-v3.0",
    cohere_api_key=env.COHERE_API_KEY,
)

rl = SemanticRouter(routes=routes, encoder=encoder, auto_sync="local")

print(rl("Shorty, you're my angel, you're my darling angel Girl, you're my friend when I'm in need, lady"))