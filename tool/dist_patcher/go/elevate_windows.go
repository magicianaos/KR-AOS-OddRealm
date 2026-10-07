//go:build windows

package main

import (
	"fmt"
	"os"
	"path/filepath"
	"syscall"
	"unsafe"
)

// 해당 폴더에 파일을 만들 수 있는지 실제로 시도해 본다.
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

// 관리자 권한으로 자기 자신을 다시 실행한다 (UAC 창이 뜬다).
func relaunchElevated(game string, extra []string) error {
	exe, err := os.Executable()
	if err != nil {
		return err
	}
	args := fmt.Sprintf("\"%s\" --elevated", game)
	for _, e := range extra {
		args += " " + e
	}

	verb, _ := syscall.UTF16PtrFromString("runas")
	file, _ := syscall.UTF16PtrFromString(exe)
	parm, _ := syscall.UTF16PtrFromString(args)
	dir, _ := syscall.UTF16PtrFromString(filepath.Dir(exe))

	r, _, e := syscall.NewLazyDLL("shell32.dll").NewProc("ShellExecuteW").Call(
		0,
		uintptr(unsafe.Pointer(verb)),
		uintptr(unsafe.Pointer(file)),
		uintptr(unsafe.Pointer(parm)),
		uintptr(unsafe.Pointer(dir)),
		1, // SW_SHOWNORMAL
	)
	if r <= 32 {
		return fmt.Errorf("권한 상승이 취소되었거나 실패했습니다 (%d, %v)", r, e)
	}
	return nil
}
