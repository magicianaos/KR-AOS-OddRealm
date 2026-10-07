//go:build !windows

package main

import (
	"errors"
	"os"
	"path/filepath"
)

func canWrite(dir string) bool {
	p := filepath.Join(dir, ".orkp_write_test")
	f, err := os.OpenFile(p, os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return false
	}
	f.Close()
	os.Remove(p)
	return true
}

func relaunchElevated(game string, extra []string) error {
	return errors.New("이 플랫폼에서는 지원되지 않습니다")
}
