// Odd Realm 한글패치 설치기
// 게임 파일을 재배포하지 않고, 사용자의 원본 파일에 변경분만 적용한다.
package main

import (
	"bufio"
	"bytes"
	"compress/zlib"
	"crypto/sha256"
	_ "embed"
	"encoding/binary"
	"encoding/hex"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

//go:embed patch.orkp
var patchData []byte

const (
	appName    = "Odd Realm 한글패치"
	appVersion = "1.0.3"
	backupDir  = "_KoreanPatch_Backup"
)

type entry struct {
	Rel     string
	SrcHash [32]byte
	DstHash [32]byte
	SrcSize uint64
	DstSize uint64
	Ops     []byte
}

// ---------- 콘솔 ----------

var stdin = bufio.NewReader(os.Stdin)

func ask(prompt string) string {
	fmt.Print(prompt)
	s, _ := stdin.ReadString('\n')
	return strings.TrimSpace(strings.Trim(s, "\"'"))
}

func pause() {
	fmt.Print("\n계속하려면 Enter 키를 누르세요...")
	stdin.ReadString('\n')
}

func fail(format string, a ...any) {
	fmt.Printf("\n[오류] "+format+"\n", a...)
	pause()
	os.Exit(1)
}

// ---------- 패치 파일 파싱 ----------

func parsePatch(raw []byte) ([]entry, error) {
	if len(raw) < 16 || string(raw[:8]) != "ORKP1\x00\x00\x00" {
		return nil, fmt.Errorf("패치 데이터 형식이 올바르지 않습니다")
	}
	want := binary.LittleEndian.Uint64(raw[8:16])
	zr, err := zlib.NewReader(bytes.NewReader(raw[16:]))
	if err != nil {
		return nil, err
	}
	body, err := io.ReadAll(zr)
	if err != nil {
		return nil, err
	}
	if uint64(len(body)) != want {
		return nil, fmt.Errorf("패치 데이터가 손상되었습니다")
	}
	r := bytes.NewReader(body)
	var n uint32
	if err := binary.Read(r, binary.LittleEndian, &n); err != nil {
		return nil, err
	}
	out := make([]entry, 0, n)
	for i := uint32(0); i < n; i++ {
		var pl uint16
		if err := binary.Read(r, binary.LittleEndian, &pl); err != nil {
			return nil, err
		}
		pb := make([]byte, pl)
		if _, err := io.ReadFull(r, pb); err != nil {
			return nil, err
		}
		var e entry
		e.Rel = string(pb)
		if _, err := io.ReadFull(r, e.SrcHash[:]); err != nil {
			return nil, err
		}
		if _, err := io.ReadFull(r, e.DstHash[:]); err != nil {
			return nil, err
		}
		if err := binary.Read(r, binary.LittleEndian, &e.SrcSize); err != nil {
			return nil, err
		}
		if err := binary.Read(r, binary.LittleEndian, &e.DstSize); err != nil {
			return nil, err
		}
		var bl uint32
		if err := binary.Read(r, binary.LittleEndian, &bl); err != nil {
			return nil, err
		}
		e.Ops = make([]byte, bl)
		if _, err := io.ReadFull(r, e.Ops); err != nil {
			return nil, err
		}
		out = append(out, e)
	}
	return out, nil
}

// ---------- 델타 적용 ----------

func applyDelta(src, ops []byte, dstSize uint64) ([]byte, error) {
	dst := make([]byte, 0, dstSize)
	r := bytes.NewReader(ops)
	var n uint32
	if err := binary.Read(r, binary.LittleEndian, &n); err != nil {
		return nil, err
	}
	for i := uint32(0); i < n; i++ {
		kind, err := r.ReadByte()
		if err != nil {
			return nil, err
		}
		switch kind {
		case 1:
			var off uint64
			var l uint32
			binary.Read(r, binary.LittleEndian, &off)
			binary.Read(r, binary.LittleEndian, &l)
			if off+uint64(l) > uint64(len(src)) {
				return nil, fmt.Errorf("델타 범위 오류")
			}
			dst = append(dst, src[off:off+uint64(l)]...)
		case 2:
			var l uint32
			binary.Read(r, binary.LittleEndian, &l)
			buf := make([]byte, l)
			if _, err := io.ReadFull(r, buf); err != nil {
				return nil, err
			}
			dst = append(dst, buf...)
		default:
			return nil, fmt.Errorf("알 수 없는 델타 명령 %d", kind)
		}
	}
	if uint64(len(dst)) != dstSize {
		return nil, fmt.Errorf("결과 크기 불일치 (%d != %d)", len(dst), dstSize)
	}
	return dst, nil
}

// ---------- 게임 경로 찾기 ----------

func looksLikeGame(dir string) bool {
	if dir == "" {
		return false
	}
	if _, err := os.Stat(filepath.Join(dir, "OddRealm.exe")); err == nil {
		return true
	}
	if st, err := os.Stat(filepath.Join(dir, "OddRealm_Data")); err == nil && st.IsDir() {
		return true
	}
	return false
}

func steamLibraries() []string {
	var roots []string
	seen := map[string]bool{}
	addVDF := func(vdf string) {
		b, err := os.ReadFile(vdf)
		if err != nil {
			return
		}
		for _, line := range strings.Split(string(b), "\n") {
			line = strings.TrimSpace(line)
			if !strings.HasPrefix(line, "\"path\"") {
				continue
			}
			parts := strings.Split(line, "\"")
			if len(parts) >= 4 {
				p := strings.ReplaceAll(parts[3], "\\\\", "\\")
				if !seen[p] {
					seen[p] = true
					roots = append(roots, p)
				}
			}
		}
	}
	bases := []string{
		`C:\Program Files (x86)\Steam`,
		`C:\Program Files\Steam`,
		`C:\Steam`,
	}
	for _, d := range "DEFGHIJKL" {
		bases = append(bases, string(d)+`:\Steam`, string(d)+`:\SteamLibrary`)
	}
	for _, b := range bases {
		if !seen[b] {
			seen[b] = true
			roots = append(roots, b)
		}
		addVDF(filepath.Join(b, "steamapps", "libraryfolders.vdf"))
		addVDF(filepath.Join(b, "config", "libraryfolders.vdf"))
	}
	return roots
}

func findGame() string {
	// 1) 실행 파일 위치 및 그 상위
	if exe, err := os.Executable(); err == nil {
		d := filepath.Dir(exe)
		for i := 0; i < 3; i++ {
			if looksLikeGame(d) {
				return d
			}
			d = filepath.Dir(d)
		}
	}
	// 2) 현재 디렉터리
	if wd, err := os.Getwd(); err == nil && looksLikeGame(wd) {
		return wd
	}
	// 3) Steam 라이브러리
	for _, lib := range steamLibraries() {
		p := filepath.Join(lib, "steamapps", "common", "Odd Realm")
		if looksLikeGame(p) {
			return p
		}
	}
	return ""
}

// ---------- 도우미 ----------

func sha(b []byte) [32]byte { return sha256.Sum256(b) }

func short(h [32]byte) string { return hex.EncodeToString(h[:4]) }

func writeAtomic(path string, data []byte) error {
	tmp := path + ".ortmp"
	if err := os.WriteFile(tmp, data, 0644); err != nil {
		return err
	}
	if err := os.Remove(path); err != nil && !os.IsNotExist(err) {
		os.Remove(tmp)
		return err
	}
	if err := os.Rename(tmp, path); err != nil {
		return err
	}
	return nil
}

// ---------- 동작 ----------

type state int

const (
	stOriginal state = iota
	stPatched
	stUnknown
	stMissing
)

func inspect(game string, es []entry) map[string]state {
	m := map[string]state{}
	for _, e := range es {
		b, err := os.ReadFile(filepath.Join(game, filepath.FromSlash(e.Rel)))
		if err != nil {
			m[e.Rel] = stMissing
			continue
		}
		h := sha(b)
		switch {
		case h == e.SrcHash:
			m[e.Rel] = stOriginal
		case h == e.DstHash:
			m[e.Rel] = stPatched
		default:
			m[e.Rel] = stUnknown
		}
	}
	return m
}

// 이전 버전 백업 폴더까지 뒤져서 원본과 일치하는 백업을 찾는다.
func findBackup(game, name string, want [32]byte) []byte {
	root := filepath.Join(game, backupDir)
	ents, err := os.ReadDir(root)
	if err != nil {
		return nil
	}
	for _, d := range ents {
		if !d.IsDir() {
			continue
		}
		b, err := os.ReadFile(filepath.Join(root, d.Name(), name))
		if err != nil {
			continue
		}
		if sha(b) == want {
			return b
		}
	}
	return nil
}

// 구버전 한글패치가 적용된 파일을 백업본으로 되돌린다.
func autoRestore(game string, es []entry, st map[string]state) bool {
	did := false
	for _, e := range es {
		if st[e.Rel] != stUnknown {
			continue
		}
		b := findBackup(game, filepath.Base(e.Rel), e.SrcHash)
		if b == nil {
			continue
		}
		if !did {
			fmt.Println("\n이전 버전 한글패치가 발견되었습니다. 원본으로 되돌리는 중...")
			did = true
		}
		full := filepath.Join(game, filepath.FromSlash(e.Rel))
		if err := writeAtomic(full, b); err != nil {
			fail("되돌리기 실패 (%s): %v\n게임이 실행 중이면 종료하고, 관리자 권한으로 실행해 보세요.", filepath.Base(e.Rel), err)
		}
		fmt.Printf("   - %s : 원본 복구\n", filepath.Base(e.Rel))
		st[e.Rel] = stOriginal
	}
	return did
}

func install(game string, es []entry) {
	st := inspect(game, es)
	autoRestore(game, es, st)
	var bad []string
	allPatched := true
	for _, e := range es {
		switch st[e.Rel] {
		case stMissing:
			bad = append(bad, e.Rel+"  (파일 없음)")
		case stUnknown:
			bad = append(bad, e.Rel+"  (다른 버전이거나 이미 다른 패치가 적용됨)")
		}
		if st[e.Rel] != stPatched {
			allPatched = false
		}
	}
	if len(bad) > 0 {
		fmt.Println("\n다음 파일이 이 패치가 지원하는 원본과 다릅니다:")
		for _, b := range bad {
			fmt.Println("   - " + b)
		}
		fmt.Println("\n이 패치는 특정 게임 버전에만 적용됩니다.")
		fmt.Println("Steam → Odd Realm 우클릭 → 속성 → 설치된 파일 → 파일 무결성 검사")
		fmt.Println("를 실행해 원본으로 되돌린 뒤 다시 시도해 주세요.")
		fail("설치를 중단했습니다.")
	}
	if allPatched {
		fmt.Println("\n이미 한글패치가 적용되어 있습니다.")
		return
	}

	bdir := filepath.Join(game, backupDir, "v"+appVersion)
	if err := os.MkdirAll(bdir, 0755); err != nil {
		fail("백업 폴더를 만들 수 없습니다: %v\n관리자 권한으로 실행해 보세요.", err)
	}

	fmt.Println()
	for i, e := range es {
		full := filepath.Join(game, filepath.FromSlash(e.Rel))
		name := filepath.Base(e.Rel)
		fmt.Printf("[%d/%d] %s\n", i+1, len(es), name)

		if st[e.Rel] == stPatched {
			fmt.Println("       이미 적용됨, 건너뜁니다")
			continue
		}
		src, err := os.ReadFile(full)
		if err != nil {
			fail("읽기 실패: %v", err)
		}

		// 백업 (이미 있으면 유지)
		bpath := filepath.Join(bdir, name)
		if _, err := os.Stat(bpath); os.IsNotExist(err) {
			fmt.Println("       원본 백업 중...")
			if err := os.WriteFile(bpath, src, 0644); err != nil {
				fail("백업 실패: %v\n관리자 권한으로 실행해 보세요.", err)
			}
		}

		fmt.Println("       패치 적용 중...")
		dst, err := applyDelta(src, e.Ops, e.DstSize)
		if err != nil {
			fail("패치 적용 실패 (%s): %v", name, err)
		}
		if sha(dst) != e.DstHash {
			fail("패치 결과 검증 실패 (%s)", name)
		}
		if err := writeAtomic(full, dst); err != nil {
			fail("쓰기 실패: %v\n게임이 실행 중이면 종료하고, 관리자 권한으로 실행해 보세요.", err)
		}
		fmt.Println("       완료")
	}
	fmt.Println("\n한글패치 설치가 끝났습니다. 게임을 실행하세요.")
	fmt.Printf("원본 파일은 %s 에 백업되어 있습니다.\n", filepath.Join(backupDir, "v"+appVersion))
}

func mustRead(p string) []byte { b, _ := os.ReadFile(p); return b }

func restore(game string, es []entry) {
	n := 0
	fmt.Println()
	for _, e := range es {
		full := filepath.Join(game, filepath.FromSlash(e.Rel))
		name := filepath.Base(e.Rel)
		b := findBackup(game, name, e.SrcHash)
		if b == nil {
			fmt.Printf("   - %s : 쓸 수 있는 백업이 없습니다 (건너뜀)\n", name)
			continue
		}
		if sha(b) == sha(mustRead(full)) {
			fmt.Printf("   - %s : 이미 원본입니다\n", name)
			continue
		}
		if err := writeAtomic(full, b); err != nil {
			fail("복구 실패 (%s): %v", name, err)
		}
		fmt.Printf("   - %s : 복구 완료\n", name)
		n++
	}
	if n == 0 {
		fmt.Println("\n복구한 파일이 없습니다.")
		fmt.Println("Steam → 속성 → 설치된 파일 → 파일 무결성 검사로도 원본을 되돌릴 수 있습니다.")
	} else {
		fmt.Printf("\n%d개 파일을 원본으로 되돌렸습니다.\n", n)
	}
}

func status(game string, es []entry) {
	st := inspect(game, es)
	names := make([]string, 0, len(es))
	for _, e := range es {
		names = append(names, e.Rel)
	}
	sort.Strings(names)
	fmt.Println()
	for _, rel := range names {
		var s string
		switch st[rel] {
		case stOriginal:
			s = "원본"
		case stPatched:
			s = "한글패치 적용됨"
		case stUnknown:
			s = "알 수 없음 (버전 불일치)"
		case stMissing:
			s = "파일 없음"
		}
		fmt.Printf("   %-46s  %s\n", filepath.Base(rel), s)
	}
}

func main() {
	enableUTF8Console()
	fmt.Printf("\n=== %s v%s ===\n", appName, appVersion)
	fmt.Println("Unity 6000.4.4f1 / Odd Realm 대응")

	es, err := parsePatch(patchData)
	if err != nil {
		fail("%v", err)
	}

	game := ""
	if len(os.Args) > 1 && !strings.HasPrefix(os.Args[1], "-") {
		game = os.Args[1]
	}
	if game == "" {
		game = findGame()
	}
	if !looksLikeGame(game) {
		fmt.Println("\nOdd Realm 설치 폴더를 자동으로 찾지 못했습니다.")
		fmt.Println("예) C:\\Program Files (x86)\\Steam\\steamapps\\common\\Odd Realm")
		for i := 0; i < 3; i++ {
			game = ask("\n게임 폴더 경로를 붙여넣고 Enter: ")
			if looksLikeGame(game) {
				break
			}
			fmt.Println("   그 폴더에서 OddRealm.exe 를 찾을 수 없습니다.")
			game = ""
		}
	}
	if !looksLikeGame(game) {
		fail("게임 폴더를 찾지 못했습니다.")
	}
	fmt.Printf("\n게임 폴더: %s\n", game)

	// 쓰기 권한 확인. 없으면 관리자 권한으로 다시 실행한다.
	elevated := false
	for _, a := range os.Args[1:] {
		if a == "--elevated" {
			elevated = true
		}
	}
	if !canWrite(game) || !canWrite(filepath.Join(game, "OddRealm_Data")) {
		if elevated {
			fail("관리자 권한으로 실행했는데도 게임 폴더에 쓸 수 없습니다.\n" +
				"게임이 실행 중이면 종료한 뒤 다시 시도해 주세요.")
		}
		fmt.Println("\n이 폴더에 쓰려면 관리자 권한이 필요합니다.")
		fmt.Println("권한 상승 창(UAC)이 뜨면 [예] 를 눌러 주세요.")
		if ask("\n관리자 권한으로 다시 실행할까요? (Y/n): ") == "n" {
			fmt.Println("\n취소했습니다. 이 파일을 우클릭 → [관리자 권한으로 실행] 해도 됩니다.")
			pause()
			return
		}
		// 설치/복구 옵션을 그대로 물려준다
		var pass []string
		for _, a := range os.Args[1:] {
			switch a {
			case "-i", "--install", "-u", "--restore", "--uninstall":
				pass = append(pass, a)
			}
		}
		if err := relaunchElevated(game, pass); err != nil {
			fail("%v\n이 파일을 우클릭 → [관리자 권한으로 실행] 해 주세요.", err)
		}
		return
	}

	for _, a := range os.Args[1:] {
		switch a {
		case "-i", "--install":
			install(game, es)
			pause()
			return
		case "-u", "--restore", "--uninstall":
			restore(game, es)
			pause()
			return
		}
	}

	for {
		status(game, es)
		fmt.Println("\n  1) 한글패치 설치")
		fmt.Println("  2) 원본으로 되돌리기")
		fmt.Println("  3) 종료")
		switch ask("\n번호 선택: ") {
		case "1":
			install(game, es)
			pause()
			return
		case "2":
			restore(game, es)
			pause()
			return
		case "3", "":
			return
		default:
			fmt.Println("  1, 2, 3 중에서 선택하세요.")
		}
	}
}
