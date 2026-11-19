from sqlalchemy import Integer, String, Text, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")

    user_sub: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    priority: Mapped[str] = mapped_column(
        String(10), nullable=False, default="Medium"
    )

    due_date: Mapped[Date | None] = mapped_column(Date, nullable=True)

    project: Mapped[str] = mapped_column(
        String(100), nullable=False, default="General"
    )