# Seguridad de la demo con login · Caso 05

**Qué demuestra:** que cada persona ve solo lo que le corresponde, y que **el filtro lo hace la base, no la página**. La página (`03_tableros/demo_login.html`, 43 KB) no lleva datos adentro: los pide con la sesión del usuario y la base devuelve solo sus filas.

## Arquitectura

```
Navegador (HTML estático)  ──login──▶  Supabase Auth  (usuario + contraseña → sesión)
        │                                   │
        └──consulta con la sesión──▶  Postgres con seguridad por fila (RLS)
                                        └─ devuelve solo las filas del alcance del usuario
```

- **Base:** Supabase, proyecto `caso05-cadena-demo` (plan gratuito, región São Paulo).
- **Clave que va en la página:** la *publicable* (`sb_publishable_…`), pensada para estar en el navegador. Sola no da acceso a nada: sin sesión, la base no devuelve filas. La clave secreta (service role) **nunca** sale del panel de Supabase.

## Quién ve qué (lo comprobó la prueba automática)

| Usuario de prueba | Rol | Filas de resultados que recibe | Locales | Incidentes |
|---|---|---|---|---|
| direccion@cadena-demo.test | Dirección | 2.484 (todas) | 12 | 110 |
| regional.norte@cadena-demo.test | Gerente regional | 864 | 4 (región Norte) | 42 |
| local.l07@cadena-demo.test | Gerente de local | 216 | 1 (L07) | 11 |
| supervisor.l03@cadena-demo.test | Supervisor | **0** (no ve números económicos) | — | 9 (solo L03) |

Contraseña de todos: `Caso05-Demo`. Datos ficticios. Los números son de **solo lectura**. Hay solo dos escrituras permitidas: el gerente de local carga explicaciones de desvío de **su** local, y el supervisor o el gerente cargan reportes de primera línea de su local. Ninguna regla permite modificar ni borrar.

## Cómo está hecho (resumen del SQL en `02_codigo/supabase_esquema.sql`)

1. **Tabla `perfiles`:** une cada usuario de login con su rol, su región y su local.
2. **Funciones de ayuda** en un esquema privado (`app`), no expuesto por la API: `mi_rol()`, `mi_region()`, `mi_local()`, `puede_ver_local(local)`.
3. **RLS activado en todas las tablas.** Ejemplo de regla:
   ```sql
   create policy "ve sus locales" on fact_resultados for select to authenticated
     using ((select app.puede_ver_local(local_id)));
   ```
4. **Promedios sin detalle:** `promedio_red()` y `promedio_formato()` devuelven solo totales agregados, para comparar contra la red sin ver otros locales. El de formato solo informa grupos de **3 o más locales**: con 2, el promedio delataría al otro. Las dos funciones son `security definer` a propósito (el asesor de Supabase lo marca como aviso y está revisado).

## Límites conocidos (y qué haría en producción)

| Límite de la demo | En producción |
|---|---|
| Los usuarios de prueba pueden cambiarse la contraseña (Supabase lo permite a cualquier usuario logueado) y dejar la demo sin acceso | Usuarios reales, cada uno con la suya; recuperación por mail |
| El registro de usuarios nuevos está abierto. Un desconocido podría crear una cuenta, pero sin perfil no ve ningún dato | Desactivar "Allow new users to sign up" (Authentication → Sign In / Providers) y dar las altas desde un proceso controlado |
| "Protección contra contraseñas filtradas" apagada | Activarla (Authentication → Policies) |
| El plan gratuito pausa el proyecto tras 1 semana sin uso; se reactiva con un clic | Plan pago (USD 25/mes) o servidor propio |
| La carga de datos se hizo con un usuario temporal con permiso de escritura **solo para él**, que se eliminó al terminar | Carga por un proceso de Sistemas con cuenta de servicio, nunca desde la página |
