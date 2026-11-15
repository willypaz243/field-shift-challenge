from sqlmodel import Field, SQLModel


class Crop(SQLModel, table=True):
    __tablename__ = "crops"

    id: str = Field(primary_key=True)
    nombre: str
    t_opt_min: float | None = None
    t_opt_max: float | None = None
    tol_helada: str | None = None
    demanda_agua: str | None = None
    deficit_tol: str | None = None
    ciclo_min_dias: int | None = None
    ciclo_max_dias: int | None = None
    fix_n: bool = False
    mercado: str | None = None
    breaks_pest_cycle: bool = False
    forage_value: str | None = None
    drought_tolerant: str | None = None
    deep_rooting: bool = False
    erosion_sens: str | None = None
    kc_inicial: float | None = None
    kc_medio: float | None = None
    kc_final: float | None = None
    altitud: str | None = None
    rotacion: str | None = None
    foto_url: str | None = None
