# Choclito - Frontend Application

Documentación técnica del frontend para la aplicación móvil Choclito, desarrollada en el marco del NASA Space Apps Challenge (Field Shift). El sistema está diseñado con una arquitectura offline-first para la gestión de parcelas agrícolas, registro de cultivos y recepción de alertas climáticas tempranas.

## Stack Tecnológico

*   **Framework:** React Native y Expo (SDK 58).
*   **Enrutamiento:** Expo Router (File-based routing).
*   **Lenguaje:** TypeScript.
*   **Sistema de Diseño:** Implementación de tokens personalizados, tipografía Atkinson Hyperlegible Next y cumplimiento de métricas de accesibilidad UI (Touch targets >= 56px, fuentes >= 17px).

## Arquitectura y Estándares

El código fuente obedece a estrictos lineamientos de ingeniería y control de calidad establecidos por el equipo:

*   **Paradigma Orientado a Objetos (OOP):** Componentización estructurada estrictamente mediante clases ES6.
*   **Modularización:** Separación de responsabilidades en directorios dedicados (`/components`, `/config`, `/constants`).
*   **Restricciones de Complejidad Ciclomática:** Límite máximo de 100 líneas por archivo y 7 líneas por método para garantizar la escalabilidad y mantenibilidad.

## Instrucciones de Ejecución

### 1. Instalación de dependencias
Desde la raíz del directorio `app/`, inicializar el entorno:

```bash
npm install