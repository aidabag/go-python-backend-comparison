package sql

import "embed"

// Встраивание скриптов инициализации БД
//
//go:embed *.sql migrations/*.sql seed/*.sql
var SQLFiles embed.FS
