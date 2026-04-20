package metrics

import (
	"strconv"
	"strings"
)

// Очистка сетевого пути (замена числовых ID на маску :id) для предотвращения всплесков кардинальности метрик
func normalizePath(p string) string {
	parts := strings.Split(p, "/")
	for i, seg := range parts {
		if seg == "" {
			continue
		}
		// Подмена числового сегмента заглушкой
		if _, err := strconv.Atoi(seg); err == nil {
			parts[i] = ":id"
			continue
		}
	}
	return strings.Join(parts, "/")
}
