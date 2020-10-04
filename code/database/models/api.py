"""
class corsicaError(Base):
    __tablename__ = 'corsica_error'

    id = Column(Integer, primary_key=True)
    time = Column(DateTime, nullable=False)
    try_id = Column(Integer, nullable=False)
    url = Column(String(512), nullable=False)
    line_number = Column(Integer, nullable=False)
    error = Column(Text, nullable=False)


class corsicaFeedback(Base):
    __tablename__ = 'corsica_feedback'

    id = Column(Integer, primary_key=True)
    time = Column(DateTime, nullable=False)
    try_id = Column(Integer, nullable=False)
    username = Column(String(512), nullable=False)
    email = Column(String(512), nullable=False)
    text = Column(Text, nullable=False)


class corsicaResultAll(Base):
    __tablename__ = 'corsica_result_all'

    id = Column(Integer, primary_key=True)
    try_id = Column(Integer, nullable=False)
    time = Column(DateTime, nullable=False)
    local_ip = Column(String(100), nullable=False)
    device = Column(Integer, nullable=False)
    device_name = Column(String(500), nullable=False)


class corsicaResultContact(Base):
    __tablename__ = 'corsica_result_contact'

    id = Column(Integer, primary_key=True)
    time = Column(DateTime, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)


class corsicaResultCorrect(Base):
    __tablename__ = 'corsica_result_correct'

    id = Column(Integer, primary_key=True)
    try_id = Column(Integer, nullable=False)
    time = Column(DateTime, nullable=False)
    local_ip = Column(String(100), nullable=False)
    device = Column(Integer, nullable=False)
    device_name = Column(String(500), nullable=False)


class corsicaResultCustom(Base):
    __tablename__ = 'corsica_result_custom'

    id = Column(Integer, primary_key=True)
    try_id = Column(Integer, nullable=False)
    time = Column(DateTime, nullable=False)
    device_name = Column(String(512), nullable=False)


class corsicaResultDnsSucces(Base):
    __tablename__ = 'corsica_result_dns_success'

    id = Column(Integer, primary_key=True)
    try_id = Column(Integer, nullable=False)
    time = Column(DateTime, nullable=False)
    duration = Column(Integer, nullable=False, server_default=text("0"))


class corsicaResultDnsTry(Base):
    __tablename__ = 'corsica_result_dns_try'

    id = Column(Integer, primary_key=True)
    try_id = Column(Integer, nullable=False)
    time = Column(DateTime, nullable=False)


class corsicaResultTry(Base):
    __tablename__ = 'corsica_result_try'

    id = Column(Integer, primary_key=True)
    time = Column(DateTime, nullable=False)
    local_ip = Column(String(100), nullable=False)
    sid = Column(String(250), nullable=False)
    duration = Column(Integer, nullable=False, server_default=text("0"))



"""
