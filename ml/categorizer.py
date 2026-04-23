from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import re

# Training data: (text, category)
TRAINING_DATA = [
    # Billing
    ("wrong charge on my bill", "Billing"),
    ("overcharged for service", "Billing"),
    ("payment not processed", "Billing"),
    ("invoice incorrect amount", "Billing"),
    ("refund not received", "Billing"),
    ("double charged my account", "Billing"),
    ("billing error on statement", "Billing"),

    # Technical
    ("app not working", "Technical"),
    ("website is down", "Technical"),
    ("cannot login to account", "Technical"),
    ("software crash error", "Technical"),
    ("bug in the system", "Technical"),
    ("server not responding", "Technical"),
    ("error message on screen", "Technical"),
    ("feature not functioning", "Technical"),

    # Service
    ("poor customer service", "Service"),
    ("staff was rude", "Service"),
    ("slow response from support", "Service"),
    ("no one answered my call", "Service"),
    ("bad experience with agent", "Service"),
    ("service quality is poor", "Service"),
    ("support team unhelpful", "Service"),

    # Delivery
    ("package not delivered", "Delivery"),
    ("order delayed", "Delivery"),
    ("wrong item received", "Delivery"),
    ("shipment lost", "Delivery"),
    ("delivery took too long", "Delivery"),
    ("parcel damaged on arrival", "Delivery"),

    # Account
    ("cannot access my account", "Account"),
    ("account suspended wrongly", "Account"),
    ("password reset not working", "Account"),
    ("profile update failed", "Account"),
    ("account details incorrect", "Account"),
]

# Priority keywords (rule-based scoring)
HIGH_PRIORITY_KEYWORDS = [
    'urgent', 'immediately', 'critical', 'emergency', 'asap',
    'fraud', 'hack', 'stolen', 'illegal', 'severe', 'serious',
    'rape', 'ragged', 'ragging', 'abuse', 'harassment', 'assault',
    'threat', 'violence', 'bullying', 'misconduct', 'discrimination',
    'not working', 'broken', 'failed', 'failure', 'crash', 'crashed',
    'cannot access', 'locked out', 'suspended', 'blocked', 'lost',
    'damaged', 'wrong charge', 'overcharged', 'double charged',
    'no response', 'ignored', 'escalate', 'unacceptable', 'terrible',
    'money', 'payment failed', 'refund', 'data loss', 'security'
]

LOW_PRIORITY_KEYWORDS = [
    'minor', 'small', 'whenever', 'not urgent', 'low priority',
    'suggestion', 'feedback', 'improvement', 'just wanted to',
    'whenever possible', 'no rush', 'general inquiry', 'question'
]

# Auto-assignment rules: keyword → department
DEPARTMENT_KEYWORDS = {
    'Cyber Crime Cell': ['hack', 'hacked', 'cyber', 'phishing', 'scam', 'fraud', 'stolen data', 'identity theft'],
    'Police Department': ['rape', 'assault', 'violence', 'threat', 'abuse', 'harassment', 'stolen', 'theft', 'crime', 'illegal'],
    'Women & Child Welfare': ['ragging', 'ragged', 'bullying', 'misconduct', 'discrimination', 'child', 'women'],
    'Billing': ['bill', 'billing', 'invoice', 'overcharged', 'payment', 'refund', 'charge', 'double charged'],
    'IT Support': ['app', 'website', 'software', 'bug', 'crash', 'error', 'login', 'server', 'technical', 'not working'],
    'Water Supply': ['water', 'pipe', 'leakage', 'no water', 'water supply', 'drainage'],
    'Electricity Department': ['electricity', 'power cut', 'electric', 'voltage', 'no power', 'light'],
    'Road Department': ['road', 'pothole', 'street', 'highway', 'traffic', 'footpath', 'bridge'],
    'Sanitation & Waste': ['garbage', 'waste', 'trash', 'sanitation', 'sewage', 'dirty', 'cleaning'],
    'Animal Welfare': ['animal', 'dog', 'stray', 'cattle', 'bird', 'pet', 'wildlife'],
    'Public Health': ['hospital', 'health', 'medical', 'disease', 'doctor', 'clinic', 'medicine'],
    'Transport Department': ['bus', 'transport', 'vehicle', 'auto', 'taxi', 'train', 'metro'],
    'Education Department': ['school', 'college', 'teacher', 'student', 'education', 'exam', 'university'],
    'Environment Department': ['pollution', 'noise', 'smoke', 'environment', 'tree', 'forest', 'air quality'],
    'Municipal Corporation': ['municipality', 'civic', 'building', 'construction', 'permit', 'license'],
    'Customer Service': ['service', 'staff', 'rude', 'support', 'response', 'agent', 'helpdesk'],
    'Logistics': ['delivery', 'package', 'shipment', 'order', 'parcel', 'courier', 'dispatch'],
    'Finance': ['tax', 'fine', 'penalty', 'finance', 'loan', 'subsidy', 'grant'],
    'Legal': ['legal', 'court', 'law', 'rights', 'complaint', 'sue', 'justice'],
}

def predict_department(text: str) -> str:
    text_lower = text.lower()
    for dept, keywords in DEPARTMENT_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return dept
    return 'Unassigned'

# Category-based default priority
CATEGORY_PRIORITY = {
    'Billing': 'High',
    'Technical': 'High',
    'Account': 'High',
    'Delivery': 'Medium',
    'Service': 'Medium',
    'General': 'Low'
}

class ComplaintClassifier:
    def __init__(self):
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer(stop_words='english', ngram_range=(1, 2))),
            ('clf', MultinomialNB())
        ])
        self._train()

    def _train(self):
        texts = [t for t, _ in TRAINING_DATA]
        labels = [l for _, l in TRAINING_DATA]
        self.model.fit(texts, labels)

    def predict_category(self, text: str) -> str:
        return self.model.predict([text])[0]

    def predict_priority(self, text: str) -> str:
        text_lower = text.lower()
        # Keyword check first
        if any(kw in text_lower for kw in HIGH_PRIORITY_KEYWORDS):
            return 'High'
        if any(kw in text_lower for kw in LOW_PRIORITY_KEYWORDS):
            return 'Low'
        # Fall back to category-based priority
        category = self.predict_category(text)
        return CATEGORY_PRIORITY.get(category, 'Medium')

# Singleton instance
classifier = ComplaintClassifier()
