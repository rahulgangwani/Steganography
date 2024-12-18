#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <png.h>

#define MAX_FILENAME 256
#define MAX_MESSAGE_SIZE 1000000000

void encode_message(const char *input_image, const char *message_file, const char *output_image);
void decode_message(const char *input_image, const char *output_file);
void error(const char *message);

int main(int argc, char *argv[]) {
    clock_t start, end;
    double cpu_time_used;

    if (argc < 2 || argc > 3) {
        error("Usage: ./steganography <input_image.png> [message_file]");
    }

    start = clock();

    if (argc == 2) {
        char output_file[MAX_FILENAME];
        snprintf(output_file, sizeof(output_file), "%s_decoded.txt", argv[1]);
        decode_message(argv[1], output_file);
    } else {
        char output_image[MAX_FILENAME];
        char *dot = strrchr(argv[1], '.');
        if (dot) {
            *dot = '\0';
        }
        snprintf(output_image, sizeof(output_image), "%s_out.png", argv[1]);
        if (dot) {
            *dot = '.';
        }
        encode_message(argv[1], argv[2], output_image);
    }

    end = clock();
    cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
    printf("Execution time: %f seconds\n", cpu_time_used);

    return 0;
}

void encode_message(const char *input_image, const char *message_file, const char *output_image) {
    FILE *fp = fopen(input_image, "rb");
    if (!fp) error("Error opening input image");

    png_structp png = png_create_read_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
    if (!png) error("Error creating PNG read struct");

    png_infop info = png_create_info_struct(png);
    if (!info) error("Error creating PNG info struct");

    if (setjmp(png_jmpbuf(png))) error("Error setting jump buffer");

    png_init_io(png, fp);
    png_read_info(png, info);

    int width = png_get_image_width(png, info);
    int height = png_get_image_height(png, info);
    png_byte color_type = png_get_color_type(png, info);
    png_byte bit_depth = png_get_bit_depth(png, info);

    if (bit_depth == 16) png_set_strip_16(png);
    if (color_type == PNG_COLOR_TYPE_PALETTE) png_set_palette_to_rgb(png);
    if (color_type == PNG_COLOR_TYPE_GRAY && bit_depth < 8) png_set_expand_gray_1_2_4_to_8(png);
    if (png_get_valid(png, info, PNG_INFO_tRNS)) png_set_tRNS_to_alpha(png);
    if (color_type == PNG_COLOR_TYPE_RGB || color_type == PNG_COLOR_TYPE_GRAY || color_type == PNG_COLOR_TYPE_PALETTE)
        png_set_filler(png, 0xFF, PNG_FILLER_AFTER);
    if (color_type == PNG_COLOR_TYPE_GRAY || color_type == PNG_COLOR_TYPE_GRAY_ALPHA)
        png_set_gray_to_rgb(png);

    png_read_update_info(png, info);

    png_bytep *row_pointers = (png_bytep*)malloc(sizeof(png_bytep) * height);
    for (int y = 0; y < height; y++) {
        row_pointers[y] = (png_byte*)malloc(png_get_rowbytes(png, info));
    }

    png_read_image(png, row_pointers);

    fclose(fp);

    FILE *msg_file = fopen(message_file, "rb");
    if (!msg_file) error("Error opening message file");

    fseek(msg_file, 0, SEEK_END);
    long msg_size = ftell(msg_file);
    fseek(msg_file, 0, SEEK_SET);

    char *message = (char*)malloc(msg_size + 1);
    fread(message, 1, msg_size, msg_file);
    message[msg_size] = '\0';

    fclose(msg_file);

    int msg_len = strlen(message);
    long bit_count = 0;
    int y,x,c;
    for (y = 0; y < height && bit_count < msg_len * 8; y++) {
        png_bytep row = row_pointers[y];
        for (x = 0; x < width && bit_count < msg_len * 8; x++) {
            png_bytep px = &(row[x * 4]);
            for (c = 0; c < 3 && bit_count < msg_len * 8; c++) {
                px[c] &= 0xFE;
                px[c] |= (message[bit_count / 8] >> (7 - (bit_count % 8))) & 1;
                bit_count++;
            }
        }
    }

    printf("MESSAGE LEN: %d\n", msg_len);
    printf("BIT COUNT: %ld\n", bit_count);
    printf("H: %d  W: %d\n", y, x);

    fp = fopen(output_image, "wb");
    if (!fp) error("Error opening output image");

    png_structp png_write = png_create_write_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
    if (!png_write) error("Error creating PNG write struct");

    png_infop info_write = png_create_info_struct(png_write);
    if (!info_write) error("Error creating PNG info write struct");

    if (setjmp(png_jmpbuf(png_write))) error("Error setting jump buffer for write");

    png_init_io(png_write, fp);

    png_set_IHDR(
        png_write,
        info_write,
        width, height,
        8,
        PNG_COLOR_TYPE_RGBA,
        PNG_INTERLACE_NONE,
        PNG_COMPRESSION_TYPE_DEFAULT,
        PNG_FILTER_TYPE_DEFAULT
    );
    png_write_info(png_write, info_write);

    png_write_image(png_write, row_pointers);
    png_write_end(png_write, NULL);

    fclose(fp);

    for (int y = 0; y < height; y++) {
        free(row_pointers[y]);
    }
    free(row_pointers);

    png_destroy_write_struct(&png_write, &info_write);
    png_destroy_read_struct(&png, &info, NULL);

    free(message);

    printf("Message encoded successfully\n");
}

void decode_message(const char *input_image, const char *output_file) {
    FILE *fp = fopen(input_image, "rb");
    if (!fp) error("Error opening input image");

    png_structp png = png_create_read_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
    if (!png) error("Error creating PNG read struct");

    png_infop info = png_create_info_struct(png);
    if (!info) error("Error creating PNG info struct");

    if (setjmp(png_jmpbuf(png))) error("Error setting jump buffer");

    png_init_io(png, fp);
    png_read_info(png, info);

    int width = png_get_image_width(png, info);
    int height = png_get_image_height(png, info);
    png_byte color_type = png_get_color_type(png, info);
    png_byte bit_depth = png_get_bit_depth(png, info);

    if (bit_depth == 16) png_set_strip_16(png);
    if (color_type == PNG_COLOR_TYPE_PALETTE) png_set_palette_to_rgb(png);
    if (color_type == PNG_COLOR_TYPE_GRAY && bit_depth < 8) png_set_expand_gray_1_2_4_to_8(png);
    if (png_get_valid(png, info, PNG_INFO_tRNS)) png_set_tRNS_to_alpha(png);
    if (color_type == PNG_COLOR_TYPE_RGB || color_type == PNG_COLOR_TYPE_GRAY || color_type == PNG_COLOR_TYPE_PALETTE)
        png_set_filler(png, 0xFF, PNG_FILLER_AFTER);
    if (color_type == PNG_COLOR_TYPE_GRAY || color_type == PNG_COLOR_TYPE_GRAY_ALPHA)
        png_set_gray_to_rgb(png);

    png_read_update_info(png, info);

    png_bytep *row_pointers = (png_bytep*)malloc(sizeof(png_bytep) * height);
    for (int y = 0; y < height; y++) {
        row_pointers[y] = (png_byte*)malloc(png_get_rowbytes(png, info));
    }

    png_read_image(png, row_pointers);

    fclose(fp);

    char *message = (char*)malloc(MAX_MESSAGE_SIZE);
    if (!message) error("Error allocating memory for message");
    memset(message, 0, MAX_MESSAGE_SIZE);
    int bit_count = 0;
    int byte_count = 0;

    for (int y = 0; y < height && byte_count < MAX_MESSAGE_SIZE - 1; y++) {
        png_bytep row = row_pointers[y];
        for (int x = 0; x < width && byte_count < MAX_MESSAGE_SIZE - 1; x++) {
            png_bytep px = &(row[x * 4]);
            for (int c = 0; c < 3 && byte_count < MAX_MESSAGE_SIZE - 1; c++) {
                message[byte_count] |= (px[c] & 1) << (7 - (bit_count % 8));
                bit_count++;
                if (bit_count % 8 == 0) {
                    if (message[byte_count] == '\0') goto end_decoding;
                    byte_count++;
                }
            }
        }
    }

end_decoding:
    if (byte_count == 0) {
        free(message);
        error("No hidden message found in the image");
    }

    FILE *msg_file = fopen(output_file, "w");
    if (!msg_file) {
        free(message);
        error("Error opening output file");
    }

    fprintf(msg_file, "%s", message);
    fclose(msg_file);

    free(message);

    for (int y = 0; y < height; y++) {
        free(row_pointers[y]);
    }
    free(row_pointers);

    png_destroy_read_struct(&png, &info, NULL);

    printf("Message decoded successfully\n");
}

void error(const char *message) {
    fprintf(stderr, "Error: %s\n", message);
    exit(1);
}