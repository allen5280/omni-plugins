# OMNI Plugins

陳柏維 Allen 的 Claude 外掛市集。

## 安裝

在 Claude Code 裡依序輸入：

```
/plugin marketplace add allen5280/omni-plugins
/plugin install ai-clone-native-single-take@omni-plugins
```

也可以走 CLI（不需要進互動模式）：

```bash
claude plugin marketplace add allen5280/omni-plugins
claude plugin install ai-clone-native-single-take@omni-plugins
claude plugin list
```

## 內含

| Plugin | 說明 |
|---|---|
| `ai-clone-native-single-take` | AI 數字人原生單片完美生產系統（五層管線＋全閘＋幀修補＋成本模型） |

### ai-clone-native-single-take

輸入一段中文文案，全自動產出零瑕疵的數字人母帶 —— 本人的臉、本人的克隆聲音、手自然動、嘴型準、無多手無殘影無爆光斑，可直接進 B-roll／剪輯層。

```
文案 → L1 文案閘 → L2 克隆配音 → L3 Avatar IV → L4 全閘稽核 → L5 幀級修補 → 母帶
```

任何一層沒過就停下來報告，不硬送。內含 16 輪失敗換來的死路總表與每支影片的成本攤提模型。

| 元件 | 數量 | Token 成本 |
|---|---|---|
| Skills | 1 | 常駐 ~240 tok／觸發 ~3.9k tok |

**需要的金鑰**（放在自己的 `config/api_keys.txt`，一行一個 `key=value`，**不要進 git**）：

```
HEYGEN_API_KEY=
MINIMAX_API_KEY=
MINIMAX_VOICE_ID_DJI_CLONE=
```

## 授權

私人使用。
