# 🚀 GitHub Actions Workflow: Bump de Versión Automático

## Resumen de cambios realizados

### ✅ Funcionalidad de Bump Automático
El workflow ahora hace **bump automático de la versión patch** cada vez que se ejecuta.

### 📋 Flujo de trabajo actualizado:

1. **Versión actual**: Lee la versión actual desde `pyproject.toml`
2. **Bump automático**: Incrementa la versión patch (ej: 0.4.7 → 0.4.8)
3. **Actualiza archivos**: Modifica `pyproject.toml` con la nueva versión
4. **Commit del bump**: Hace commit del cambio de versión
5. **Push al repo**: Sube el commit a master
6. **Verifica tag**: Chequea si el tag ya existe
7. **Crea tag**: Crea el nuevo tag Git
8. **Build y test**: Construye el package y lo valida
9. **GitHub Release**: Crea el release en GitHub con changelog
10. **Publica PyPI**: Sube el package a PyPI
11. **Notifica éxito**: Muestra enlaces y confirmación

### 🔄 Estrategia de versionado:
- **Tipo**: Semantic Versioning (MAJOR.MINOR.PATCH)
- **Increment**: Patch automático (+1)
- **Formato**: X.Y.Z → X.Y.(Z+1)

### 🎯 Triggers:
- Push a `master`
- Pull Request merged a `master`

### 📝 Ejemplo de funcionamiento:

```
Versión actual: 0.4.7
      ↓
Bump automático: 0.4.8
      ↓
Commit: "chore: bump version to 0.4.8"
      ↓
Tag: v0.4.8
      ↓
Release: Release v0.4.8
      ↓
PyPI: mcp-open-client==0.4.8
```

### 🛠️ Mejoras adicionales implementadas:

1. **Action actualizada**: Reemplazada `actions/create-release@v1` (deprecated) por `softprops/action-gh-release@v1`
2. **Dependencias**: Agregada `tomli` para compatibilidad con Python < 3.11
3. **Changelog mejorado**: Muestra el bump de versión en el release notes
4. **Configuración corregida**: Arreglado `python_version` en mypy config
5. **Release notes automáticas**: Habilitado `generate_release_notes: true`

### 📊 Salida esperada:
```
🎉 Successfully released version 0.4.8 to PyPI!
📦 Package: https://pypi.org/project/mcp-open-client/0.4.8/
🏷️ GitHub Release: https://github.com/alejoair/mcp-open-client/releases/tag/v0.4.8
🔄 Version bump: 0.4.7 → 0.4.8
```

### 🚨 Importante:
- **Cada push a master** generará un nuevo release
- **La versión se incrementa automáticamente**
- **No requiere intervención manual**
- **El workflow evita releases duplicados** verificando si el tag ya existe

### 💡 Próximos pasos opcionales:
- Agregar bump de `minor` o `major` basado en commit messages
- Implementar changelog automático basado en commits
- Agregar tests antes del release
- Configurar notificaciones (Slack, Discord, etc.)
