# Format expansion measurement

The added format group contains 52 cases: 31 produced verified smaller output and 21 were
unchanged. There were no preservation failures, verifier skips or timeouts. This was one
measurement per case, so it is an effectiveness check rather than a timing benchmark.

| Added profile | Result on the measured checkout |
|---|---|
| 15 native ODF package variants, including the `.otf` formula-template route | All 15 improved; `.otf` went from 1,288 to 762 bytes. |
| Nine R serialization compound suffixes | All nine improved; `.rds.gz` went from 4,233 to 2,080 bytes. |
| CPIO newc as `.cpio`, `.cpbz2` and `.cpio.bz2` | All three improved; `.cpio` went from 622,080 to 604,904 bytes, and the compressed variants from 17,344 to 14,046 bytes. |
| Signed CRX3 extension package | Unchanged with `unsupported prepended ZIP wrapper`; the independent oracle confirmed the signature and ZIP contents. |
| Synthetic Apple CAR catalog with a weak MLEC rendition | Unchanged with `CAR CSI metadata/payload length mismatch` while validating the candidate. |

The CRX and CAR observations describe filerepack commit `2d41e71` from the local checkout, whose
working tree was dirty before and after the measurement. The source tree did not change during the
run. The corpus keeps these cases because they distinguish recognized file names from successful,
preservation-verified recompression. The measured Python source hash was
`233da25476a48c388f956dc0ec3dc1b157036f3086440c3246734f60cec3c1df`. Re-run this group after changing filerepack:

```sh
python -m frbench run --filerepack ../filerepack \
  --ext car,cpio,cpbz2,cpio.bz2,crx,odg,otg,odf,odb,odc,odi,odm,ott,ots,otp,oth,otm,otc,oti,otf,rds,rda,rdata,bz2 \
  --output results/format-expansion
```

The CRX3 fixture is generated with an ephemeral test-only RSA key. Its private key exists only in a
temporary directory; the checked-in file contains the public proof needed for independent
verification. Its ZIP payload contains a minimal Manifest V3 extension manifest and synthetic
resources.
