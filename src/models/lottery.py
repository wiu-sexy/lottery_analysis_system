from src.models.user import db
from datetime import datetime

class LotteryResult(db.Model):
    __tablename__ = 'lottery_results'
    
    id = db.Column(db.Integer, primary_key=True)
    original_id = db.Column(db.Integer, unique=True, nullable=False)  # API返回的原始ID
    type = db.Column(db.Integer, nullable=False)
    type_name = db.Column(db.String(50), nullable=False)
    issue_number = db.Column(db.String(20), nullable=False, unique=True)
    lottery_date = db.Column(db.Date, nullable=False)
    week = db.Column(db.String(10), nullable=False)
    win_code = db.Column(db.String(100), nullable=False)  # 存储完整的中奖号码字符串
    
    # 分别存储红球和蓝球
    red_balls = db.Column(db.String(50), nullable=False)  # 前6个红球号码
    blue_ball = db.Column(db.Integer, nullable=False)     # 最后一个蓝球号码
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<LotteryResult {self.issue_number}: {self.win_code}>'

    def to_dict(self):
        return {
            'id': self.id,
            'original_id': self.original_id,
            'type': self.type,
            'type_name': self.type_name,
            'issue_number': self.issue_number,
            'lottery_date': self.lottery_date.strftime('%Y-%m-%d') if self.lottery_date else None,
            'week': self.week,
            'win_code': self.win_code,
            'red_balls': self.red_balls,
            'blue_ball': self.blue_ball,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
    
    @staticmethod
    def parse_win_code(win_code_str):
        """解析中奖号码字符串，分离红球和蓝球"""
        numbers = win_code_str.split(',')
        if len(numbers) >= 7:
            red_balls = ','.join(numbers[:6])  # 前6个是红球
            blue_ball = int(numbers[6])        # 最后一个是蓝球
            return red_balls, blue_ball
        return None, None
    
    def get_red_balls_list(self):
        """获取红球号码列表"""
        return [int(x) for x in self.red_balls.split(',')]
    
    def get_all_numbers_list(self):
        """获取所有号码列表（红球+蓝球）"""
        red_list = self.get_red_balls_list()
        return red_list + [self.blue_ball]


class NumberFrequency(db.Model):
    """号码频率统计表"""
    __tablename__ = 'number_frequency'
    
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    ball_type = db.Column(db.String(10), nullable=False)  # 'red' 或 'blue'
    frequency = db.Column(db.Integer, default=0)
    last_appeared = db.Column(db.Date)
    days_since_last = db.Column(db.Integer, default=0)
    
    # 时间段统计
    frequency_1year = db.Column(db.Integer, default=0)
    frequency_2year = db.Column(db.Integer, default=0)
    frequency_3year = db.Column(db.Integer, default=0)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<NumberFrequency {self.ball_type}:{self.number} freq:{self.frequency}>'

    def to_dict(self):
        return {
            'id': self.id,
            'number': self.number,
            'ball_type': self.ball_type,
            'frequency': self.frequency,
            'last_appeared': self.last_appeared.strftime('%Y-%m-%d') if self.last_appeared else None,
            'days_since_last': self.days_since_last,
            'frequency_1year': self.frequency_1year,
            'frequency_2year': self.frequency_2year,
            'frequency_3year': self.frequency_3year,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class PredictionResult(db.Model):
    """预测结果表"""
    __tablename__ = 'prediction_results'
    
    id = db.Column(db.Integer, primary_key=True)
    prediction_date = db.Column(db.Date, nullable=False)
    predicted_issue = db.Column(db.String(20), nullable=False)
    
    # 预测的号码
    predicted_red_balls = db.Column(db.String(50), nullable=False)
    predicted_blue_ball = db.Column(db.Integer, nullable=False)
    predicted_win_code = db.Column(db.String(100), nullable=False)
    
    # 预测算法和置信度
    algorithm_used = db.Column(db.String(50), nullable=False)
    confidence_score = db.Column(db.Float, default=0.0)
    
    # 实际结果（开奖后更新）
    actual_win_code = db.Column(db.String(100))
    matches_count = db.Column(db.Integer, default=0)
    is_accurate = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<PredictionResult {self.predicted_issue}: {self.predicted_win_code}>'

    def to_dict(self):
        return {
            'id': self.id,
            'prediction_date': self.prediction_date.strftime('%Y-%m-%d') if self.prediction_date else None,
            'predicted_issue': self.predicted_issue,
            'predicted_red_balls': self.predicted_red_balls,
            'predicted_blue_ball': self.predicted_blue_ball,
            'predicted_win_code': self.predicted_win_code,
            'algorithm_used': self.algorithm_used,
            'confidence_score': self.confidence_score,
            'actual_win_code': self.actual_win_code,
            'matches_count': self.matches_count,
            'is_accurate': self.is_accurate,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

