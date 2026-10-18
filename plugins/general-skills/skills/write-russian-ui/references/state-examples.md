# State examples

Use these examples only when the stated behavior matches the product. Adapt terminology and punctuation to its existing style.

| Confirmed context | Suggested copy | Boundary |
|---|---|---|
| A button opens a folder picker; it does not begin export | «Выбрать папку» | Do not label it «Экспортировать» until that is the actual action. |
| A saved-preset collection is empty; a working create action is present | «Пресетов пока нет»; action «Создать пресет» | Do not show this state while the collection is still loading. |
| Filters hide every existing preset; a clear-filter action is present | «Нет пресетов с такими параметрами»; action «Сбросить фильтры» | Do not imply that the account contains no presets. |
| Export failed; the cause is unknown; retry is supported | «Не удалось экспортировать видео»; action «Повторить экспорт» | Do not blame a network connection or promise that unsaved changes survived. |
| A preview is being prepared; no progress estimate or cancellation exists | «Подготавливаем предпросмотр» | Do not add a countdown or a cancel control. |
| This photo-import flow requires library permission; access was denied; the app can open its system settings, where changing the permission can restore access | «Чтобы выбрать фото, разрешите доступ в настройках»; action «Открыть настройки» | Use a different next step if this flow does not require permission or settings cannot resolve the state. |
| A background save has started but completion is not confirmed | «Сохраняем изменения» | Use a success message only after the application confirms completion. |

## Localization example

Suppose the counted objects are confirmed to be layers. A wording correction can retain the existing message structure:

```json
{
  "layers.count": "{count, plural, one {# объект} few {# объекта} many {# объектов} other {# объекта}}"
}
```

```json
{
  "layers.count": "{count, plural, one {# слой} few {# слоя} many {# слоёв} other {# слоя}}"
}
```

Keep `layers.count`, `count`, every selector, and the `#` substitutions intact. The example uses «ё»; follow the actual product's convention. Check the existing parser and representative values such as 1, 2, 5, and 21. Preserve branches even when their wording looks similar: the formatter may select them differently.

For rich text, keep tags and interpolation in their existing syntax. A translator's sentence should not rename a parameter, remove an accessible link, or turn a literal escape into markup.
