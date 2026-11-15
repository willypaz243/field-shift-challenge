# Choclito — Flujo de la aplicación

Diagramas del flujo de la app según los mockups de `mockups/`. Los diagramas usan [Mermaid](https://mermaid.js.org/) y se ven directo en GitHub.

Pantallas (archivo → nombre):

| Archivo | Pantalla |
|---|---|
| `ubicar.html` | Paso 1 · ¿Tu parcela está aquí? |
| `agua.html` | Paso 2 · Tu parcela (fuente de agua + qué te importa más) |
| `hoy.html` | Hoy |
| `calendario.html` | Calendario |
| `sembrar.html` | Sembrar (carrusel de cultivos) |
| `cultivo.html` | Detalle de un cultivo + elegir fecha de siembra |
| `rotar.html` | ¿Qué sembrar después? (rotaciones) |
| `zona.html` | Mi zona (mapa, avisar algo, historial) |
| `avisos.html` | Avisos (alertas y recordatorios) |

---

## 1. Mapa de navegación

```mermaid
flowchart TD
    subgraph Inicio["Primer uso"]
        U["Paso 1<br/>¿Tu parcela está aquí?"] -->|Sí, aquí está| A["Paso 2<br/>Fuente de agua +<br/>¿Qué te importa más?"]
    end
    A -->|Listo| HOY

    subgraph Nav["Barra de navegación (4 pestañas)"]
        HOY["Hoy"]
        CAL["Calendario"]
        SEM["Sembrar"]
        ZON["Mi zona"]
    end

    HOY <--> CAL
    CAL <--> SEM
    SEM <--> ZON

    HOY -->|campana| AV["Avisos<br/>alertas + recordatorios"]
    CAL -->|campana| AV
    SEM -->|campana| AV
    ZON -->|campana| AV

    HOY -->|toca un cultivo| MC(["Ventana: Mi cultivo"])
    HOY -.->|1 día después de la cosecha| MQ(["Ventana: ¿Cómo salió<br/>tu cosecha?"])
    CAL -->|toca una semana| MS(["Ventana: pronóstico<br/>día por día"])
    CAL -->|Ver próximos meses| MM(["Ventana: próximos meses"])
    CAL -->|toca una cosecha o siembra| MC
    MM -->|toca una cosecha o siembra| MC
    MC -->|¿Qué sembrar después?| ROT["¿Qué sembrar después?"]

    SEM -->|toca un cultivo| CUL["Detalle del cultivo"]
    CUL -->|Elegir fecha de siembra| MF(["Ventana: Fecha de siembra"])
    MF -->|Planificar rotación| ROT
    ROT -->|toca un plan| MP(["Ventana: plan de rotación"])

    ZON -->|Avisar algo| MA(["Ventana: Avisar algo"])
    ZON -->|Historial| MH(["Ventana: Historial"])
```

Leyenda: rectángulo = pantalla; óvalo = ventana (bottom sheet) sobre la pantalla.

---

## 2. Primer uso (onboarding)

```mermaid
sequenceDiagram
    actor Ag as Agricultor
    participant App
    participant API

    App->>App: Pide permiso de ubicación (GPS)
    App->>API: GET /v1/parcelas/cercanas?lat&lon
    API-->>App: Parcelas del mapa + parcela más probable
    App->>Ag: Mapa con su parcela marcada
    alt No es su parcela
        Ag->>App: Toca su parcela en el mapa
    end
    Ag->>App: "Sí, aquí está"
    App->>API: POST /v1/parcelas
    API-->>App: parcela_id, zona, distrito
    App->>Ag: ¿De dónde sale tu agua? / ¿Qué te importa más?
    Ag->>App: Un toque en cada pregunta (se guarda solo)
    App->>API: PUT /v1/parcelas/{id}/perfil
    App->>Ag: Pantalla Hoy
```

---

## 3. Hoy

```mermaid
flowchart TD
    H["Abrir Hoy"] --> D["Cargar datos del día<br/>(caché si no hay señal)"]
    D --> AL{"¿Hay alerta<br/>en 7 días?"}
    AL -->|sí| BAN["Franja de alerta arriba<br/>ej. Helada el sábado · -2 °C"]
    AL -->|no| DIA
    BAN --> DIA["Tarjeta del día<br/>icono, máx/mín, lluvia, Escuchar"]
    DIA --> CUL["Mis cultivos<br/>barra de avance hasta la cosecha"]
    CUL --> REP["Tira de La Angostura (% de agua)"]
    D --> CQ{"¿Algún cultivo pasó su<br/>fecha de cosecha hace ≥1 día?"}
    CQ -->|sí| Q(["Ventana obligatoria:<br/>¿Cómo salió tu cosecha?<br/>Buena · Regular · Mala"])
    Q -->|elige| POST["POST /v1/cosechas/{id}/resultado"]
    Q -->|Todavía no coseché| LATER["Pregunta otra vez en 3 días"]
```

---

## 4. Sembrar, elegir fecha y planificar rotación

```mermaid
flowchart TD
    S["Sembrar<br/>carrusel de cultivos"] -->|etiqueta 'Mejor época'<br/>si conviene sembrar ahora| S
    S -->|toca cultivo| C["Detalle del cultivo<br/>Siembra / Cosecha / Si siembras ahora"]
    C -->|Elegir fecha de siembra| F(["Calendario mensual<br/>días buenos · con cuidado · malos"])
    F -->|toca un día| R["Veredicto + fecha de cosecha estimada"]
    R -->|Agregar a mis cultivos| ADD["POST /v1/parcelas/{id}/cultivos"]
    ADD --> HOY["Aparece en Hoy y en Calendario"]
    R -->|Planificar rotación| ROT["¿Qué sembrar después?<br/>usa la fecha de cosecha elegida"]
    ROT --> OBJ["Elige objetivo:<br/>Ahorrar agua · Mejor tierra · Forraje · Vender"]
    OBJ --> RANK["GET /v1/rotaciones<br/>plan actual + 3 alternativas<br/>'Mejor para ti' según objetivo y época"]
    RANK -->|toca un plan| P(["Ventana del plan<br/>lo bueno · revisa con tu técnico · falta saber · fuentes"])
    P -->|Quiero este plan| SAVE["POST /v1/parcelas/{id}/rotacion"]
    SAVE --> CALP["Calendario: 'Siembra de X' en su fecha<br/>Mi cultivo: 'Después: X, fecha'"]
```

---

## 5. Calendario

```mermaid
flowchart LR
    C["Calendario"] --> W["Próximas 4 semanas<br/>(pronóstico día por día)"]
    C --> E["Eventos con fecha exacta<br/>Cosecha · Siembra"]
    C --> P["Ver semanas pasadas<br/>(clima medido)"]
    C --> M["Ver próximos meses<br/>(clima típico 30 años)"]
    W -->|toca semana| WD(["7 días: icono, lluvia, máx/mín,<br/>helada, granizo"])
    E -->|toca evento| MC(["Mi cultivo<br/>+ ¿Qué sembrar después?<br/>+ Ya coseché"])
    M --> ME["Meses + eventos intercalados"]
```

Las semanas 3 y 4 se marcan como "más lejos, puede cambiar".

---

## 6. Avisos: alertas y recordatorios

```mermaid
flowchart TD
    subgraph Fuente["Datos"]
        F1["Pronóstico 28 días<br/>NASA GEOS + IMERG"]
        F2["Fechas de cosecha<br/>de mis cultivos"]
        F3["Nivel La Angostura"]
    end
    F1 --> M1{"¿Helada, granizo,<br/>lluvia fuerte?"}
    M1 -->|sí| AL["Alerta<br/>(sección Alertas, arriba)"]
    F3 --> M3{"¿Nivel bajo?"}
    M3 -->|sí| AL
    F2 --> R7["7 días antes:<br/>cosecha en 7 días"]
    F2 --> R1["1 día antes:<br/>cosecha mañana"]
    F2 --> R0["El mismo día:<br/>ya está lista para cosechar"]
    F2 --> RQ["1 día después:<br/>¿Cómo salió tu cosecha?"]
    R7 & R1 & R0 & RQ --> REC["Recordatorio<br/>(sección Recordatorios, abajo)"]
    AL & REC --> PUSH["Notificación del celular · 6:00"]
```

---

## 7. Avisar algo y Mi zona

```mermaid
sequenceDiagram
    actor Ag as Agricultor
    participant App
    participant Cola as Cola sin señal
    participant API
    participant Zona as Mapa de la zona

    Ag->>App: Mi zona → Avisar algo
    Ag->>App: Elige qué pasó (No llegó el agua, Helada, Granizo, Inundación, Plaga)
    opt Si quiere
        Ag->>App: Foto / Audio
    end
    Ag->>App: Enviar aviso
    App->>Cola: Guarda con id local
    Cola->>API: POST /v1/reportes (cuando hay señal)
    API->>Zona: Agrega el reporte sin nombre
    Zona-->>App: GET /v1/zonas/{zona}/mapa
    App->>Ag: "Aviso enviado. 7 vecinos avisaron lo mismo"
```

---

## 8. Ciclo de vida de un cultivo

```mermaid
stateDiagram-v2
    [*] --> Planificado: Quiero este plan / fecha futura
    [*] --> Sembrado: Agregar a mis cultivos
    Planificado --> Sembrado: llega la fecha de siembra
    Sembrado --> Creciendo
    Creciendo --> ListoParaCosechar: fecha de cosecha
    ListoParaCosechar --> PreguntaCosecha: +1 día
    PreguntaCosecha --> PreguntaCosecha: Todavía no (+3 días)
    PreguntaCosecha --> Calificado: Buena · Regular · Mala
    Calificado --> [*]
    Calificado --> Planificado: siguiente cultivo de la rotación
```

La alfalfa es perenne: después de cada cosecha vuelve a "Creciendo" en lugar de terminar.

---

## 9. Flujo de datos

```mermaid
flowchart LR
    subgraph NASA
        POWER["NASA POWER<br/>temp., heladas, radiación"]
        IMERG["GPM IMERG<br/>lluvia"]
        SMAP["SMAP<br/>humedad del suelo"]
        GEOS["GEOS<br/>pronóstico"]
        LS["Landsat / Sentinel-2<br/>NDVI, campo sin cultivo"]
    end
    subgraph Local
        GAMC["GAMC WMS<br/>distritos, zonas, drenaje"]
        ANG["Riego N°1<br/>nivel La Angostura"]
        FAO["FAO-56<br/>Kc y duración de cultivos"]
        REP["Reportes de agricultores"]
    end
    POWER & IMERG & SMAP & GEOS & LS --> ETL["Pipeline de analistas<br/>malla común + reglas"]
    GAMC & ANG & FAO & REP --> ETL
    ETL --> API["API Choclito<br/>(ver API-CONTRACT.md)"]
    API --> CACHE["Caché en el celular<br/>'actualizado 16 nov, 6:00'"]
    CACHE --> APP["App"]
    APP -->|reportes, cosechas, planes| API
```
