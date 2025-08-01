from datetime import datetime
from flask_app import db


class SessionLog(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, nullable=False, index=True)
    username = db.Column(db.String(100), nullable=True, index=True)  # Added username field
    query = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<SessionLog {self.id}: {self.user_id} at {self.timestamp}>"